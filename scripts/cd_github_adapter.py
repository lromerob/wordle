"""Read-only GitHubEvidenceSource using authenticated gh CLI; never prints API payloads."""
import os
import re
import shutil
import subprocess

from cd_plan_contract import REPOSITORY, RemoteTrustBlocked, decode, matching, require


class GitHubReadAdapter:
    def __init__(self, executable=None, runner=None):
        self.executable = executable or shutil.which("gh")
        require(self.executable is not None, "GitHub CLI unavailable")
        self.runner = runner or subprocess.run
        self._execute(["auth", "status", "--hostname", "github.com"])

    def _execute(self, arguments):
        env = dict(os.environ, GH_PROMPT_DISABLED="1", GH_HOST="github.com", GH_PAGER="cat")
        env.pop("GH_DEBUG", None)
        try:
            result = self.runner([self.executable, *arguments], capture_output=True, text=True,
                                 encoding="utf-8", timeout=90, check=False, env=env)
        except (OSError, subprocess.SubprocessError):
            raise RemoteTrustBlocked("GitHub CLI unavailable or request timed out") from None
        if result.returncode != 0:
            code = re.search(r"HTTP (\d{3})", result.stderr or "")
            category = code.group(1) if code else "CLI/authentication"
            raise RemoteTrustBlocked("GitHub read failed: " + category)
        return result.stdout

    def _get(self, suffix="", paginated=False):
        args = ["api", "--hostname", "github.com", "--method", "GET",
                "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2022-11-28",
                "repos/" + REPOSITORY + suffix]
        if paginated: args += ["--paginate", "--slurp"]
        try:
            return decode(self._execute(args))
        except RemoteTrustBlocked:
            raise
        except (ValueError, TypeError):
            raise RemoteTrustBlocked("Malformed GitHub response") from None

    def _object(self, suffix=""):
        value = self._get(suffix)
        require(isinstance(value, dict), "Expected GitHub object response")
        return value

    def _list(self, suffix, collection=None):
        pages = self._get(suffix + "?per_page=100", True)
        require(isinstance(pages, list) and len(pages) > 0, "Missing GitHub pages")
        items, totals = [], []
        for page in pages:
            if collection:
                require(isinstance(page, dict) and type(page.get("total_count")) is int
                        and page["total_count"] >= 0, "Missing GitHub collection count")
                totals.append(page["total_count"])
                page = page.get(collection)
            require(isinstance(page, list) and all(isinstance(item, dict) for item in page),
                    "Malformed GitHub collection")
            items.extend(page)
        if totals:
            require(all(total == len(items) for total in totals), "Incomplete or changing GitHub collection")
        ids = [item.get("id") for item in items]
        require(all(type(item) is int and item > 0 for item in ids)
                and len(set(ids)) == len(ids), "Missing or duplicated GitHub object IDs")
        return {"total_count": len(items), collection: items} if collection else items

    @staticmethod
    def _id(value):
        matching(r"[1-9][0-9]*", str(value))
        return str(value)

    def repository(self): return self._object()
    def run(self, run_id): return self._object("/actions/runs/" + self._id(run_id))

    def environment(self, name):
        matching(r"wordle-azure-(demo|infra)", name)
        return self._object("/environments/" + name)

    def branch_policies(self, name):
        matching(r"wordle-azure-(demo|infra)", name)
        return self._list("/environments/" + name + "/deployment-branch-policies", "branch_policies")

    def permission(self, login):
        require(login == "lromerob", "Unexpected approval principal")
        return self._object("/collaborators/" + login + "/permission")

    def approvals(self, run_id):
        value = self._get("/actions/runs/" + self._id(run_id) + "/approvals")
        require(isinstance(value, list) and all(isinstance(item, dict) for item in value),
                "Malformed approval history")
        return value

    def comments(self, issue):
        return self._list("/issues/" + self._id(issue) + "/comments")

    def jobs(self, run_id, attempt):
        return self._list("/actions/runs/" + self._id(run_id) + "/attempts/" + self._id(attempt) + "/jobs", "jobs")
