"""Blue-Green promotion with gates, compare-and-swap selector and automatic rollback.

No database rollback. Both previous workloads remain running. Caller owns cluster
lifecycle and supplies explicit Kubernetes context and private HTTP endpoints.
"""
import json
import time


class CandidateRejected(RuntimeError):
    pass


class PromotionController:
    def __init__(self, kube, public, candidates, record, game_path, phase):
        self.kube = kube
        self.public = public
        self.candidates = candidates
        self.record = record
        self.game_path = game_path
        self.phase = phase

    def active(self):
        service = json.loads(self.kube("get", "service", "frontend", "-o", "json").stdout)
        slot = service["spec"]["selector"]["wordle.slot"]
        if slot not in ("blue", "green"):
            raise RuntimeError("Unknown active selector; refusing promotion")
        return slot

    def switch(self, previous, target):
        # A concurrent operator must not be silently overwritten.
        patch = [{"op": "test", "path": "/spec/selector/wordle.slot", "value": previous},
                 {"op": "replace", "path": "/spec/selector/wordle.slot", "value": target}]
        self.kube("patch", "service", "frontend", "--type=json", "-p", json.dumps(patch))
        if self.active() != target:
            raise RuntimeError("Selector verification failed")
        self.record("selector_switched", previous=previous, active=target)

    def healthy(self, fetch, slot):
        for path in (self.game_path, "/api/health", "/"):
            status, release, body = fetch(path)
            if status != 200 or release != slot:
                raise RuntimeError(f"HTTP gate failed: status={status}, release={release}, expected={slot}")
            if path == "/api/health" and body != {"status": "ok"}:
                raise RuntimeError("Unexpected health contract")
            if path == self.game_path and "partida" not in body:
                raise RuntimeError("Functional game read failed")

    def await_public(self, slot, seconds=60):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                self.healthy(self.public, slot)
                return
            except Exception:
                time.sleep(.3)
        raise RuntimeError("Public path did not converge to " + slot)

    def gate(self, slot, timeout=120):
        try:
            for component in ("backend", "frontend"):
                name = component + "-" + slot
                self.kube("rollout", "status", "deployment/" + name,
                          "--timeout=" + str(timeout) + "s", timeout=timeout + 15)
                d = json.loads(self.kube("get", "deployment", name, "-o", "json").stdout)
                if d["spec"]["replicas"] != 1 or d["status"].get("updatedReplicas") != 1 or d["status"].get("availableReplicas") != 1:
                    raise RuntimeError("Latest candidate revision is not available")
                self.record("deployment_gate", name=name,
                            generation=d["metadata"]["generation"],
                            image=d["spec"]["template"]["spec"]["containers"][0]["image"])
            self.healthy(self.candidates[slot], slot)
        except Exception as error:
            raise CandidateRejected("Candidate gate failed: " + type(error).__name__) from None
        self.record("candidate_accepted", slot=slot)

    def promote(self, target, *, gate_timeout=120, after_switch=None):
        previous = self.active()
        if previous == target:
            raise ValueError("Candidate is already active")
        self.await_public(previous)
        try:
            self.gate(target, timeout=gate_timeout)
        except CandidateRejected as error:
            if self.active() != previous:
                raise RuntimeError("Selector changed during candidate rejection")
            self.healthy(self.public, previous)
            self.record("candidate_rejected_before_promotion", candidate=target,
                        stable=previous, reason=str(error), selector_unchanged=True)
            return {"outcome": "rejected", "active": previous, "reason": str(error)}
        switched = False
        try:
            self.phase("promotion-" + target)
            self.switch(previous, target)
            switched = True
            self.await_public(target)
            # HTTP observation proves that this is a real promotion, not only a patch.
            self.record("promoted_http_observed", active=target)
            if after_switch:
                after_switch()
            self.healthy(self.public, target)
            self.phase("steady-" + target)
            self.record("promotion_succeeded", previous=previous, active=target)
            return {"outcome": "promoted", "active": target}
        except Exception as error:
            if not switched:
                raise
            self.phase("rollback-" + previous)
            reason = str(error)
            self.record("post_promotion_failure", candidate=target, reason=reason)
            self.switch(target, previous)
            self.await_public(previous)
            self.record("automatic_rollback_verified", failed=target, active=previous,
                        reason=reason, database_rollback=False)
            return {"outcome": "rolled-back", "active": previous, "reason": reason}
