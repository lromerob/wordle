"""Focused offline runner configuration tests; never registers or starts a listener."""
import importlib.util
import io
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('runner_entrypoint',ROOT/'entrypoint.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)

class RunnerTests(unittest.TestCase):
    def test_default_does_not_register(self):
        with patch.object(entry.sys,'argv',['entrypoint']),patch.object(entry,'validate') as validate,patch.object(entry,'token_operation') as register:
            entry.main();validate.assert_called_once();register.assert_not_called()
    def test_registration_refuses_without_approval_before_reading_token(self):
        with patch.dict(os.environ,{},clear=True),patch.object(entry.sys,'stdin') as stream:
            with self.assertRaises(ValueError):entry.token_operation('REGISTER')
            stream.readline.assert_not_called()
    def test_activate_requires_explicit_approval(self):
        with patch.dict(os.environ,{},clear=True),patch.object(entry.sys,'argv',['entrypoint','activate']),patch.object(entry,'token_operation') as register:
            with self.assertRaises(ValueError):entry.main()
            register.assert_not_called()
    def test_root_refused(self):
        with patch.dict(os.environ,{'WORDLE_RUNNER_AUTHORIZED_ACTION':'REGISTER'}),patch.object(entry.os,'getuid',return_value=0,create=True),patch.object(entry.sys,'stdin') as stream:
            with self.assertRaises(ValueError):entry.token_operation('REGISTER')
            stream.readline.assert_not_called()
    def test_registration_exact_repo_token_not_in_arguments_or_output(self):
        captured=[]
        def configured(*args,**kwargs):
            captured.append(dict(kwargs['env']))
            return Mock(returncode=0)
        with patch.dict(os.environ,{'WORDLE_RUNNER_AUTHORIZED_ACTION':'REGISTER'}),patch.object(entry.os,'getuid',return_value=10001,create=True),patch.object(entry.sys,'stdin',io.StringIO('SYNTHETIC_NOT_A_REAL_TOKEN\n')),patch.object(entry.Path,'exists',return_value=False),patch.object(entry.subprocess,'run',side_effect=configured) as run,patch.object(entry,'require_runtime_store'):

            entry.token_operation('REGISTER')
            args=run.call_args.args[0];self.assertIn('https://github.com/lromerob/wordle',args)
            self.assertNotIn('SYNTHETIC_NOT_A_REAL_TOKEN',str(args));self.assertIn('--ephemeral',args)
            self.assertEqual(run.call_args.kwargs['stdout'],entry.subprocess.DEVNULL)
            self.assertEqual(captured[0]['ACTIONS_RUNNER_INPUT_TOKEN'],'SYNTHETIC_NOT_A_REAL_TOKEN')
            self.assertNotIn('RUNNER_INPUT_TOKEN',captured[0])
    def test_run_requires_registration_and_explicit_approval(self):
        with patch.dict(os.environ,{},clear=True),patch.object(entry.sys,'argv',['entrypoint','run']),patch.object(entry.os,'execv') as execute:
            with self.assertRaises(ValueError):entry.main()
            execute.assert_not_called()
    def test_compose_security_and_bind_contract(self):
        source=(ROOT/'compose.yaml').read_text()
        self.assertIn('create_host_path: false',source);self.assertIn('user: "10001:10001"',source)
        self.assertIn('cap_drop: [ALL]',source);self.assertNotIn('privileged: true',source)
        self.assertNotIn('/var/run/docker.sock',source);self.assertNotIn('ports:',source)
        self.assertIn('command: ["validate"]',source)
    def test_download_checksum_mismatch_is_rejected(self):
        spec=importlib.util.spec_from_file_location('runner_install',ROOT/'install_tools.py')
        installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
        with patch.object(installer,'fetch',return_value=b'synthetic-corruption'):
            with self.assertRaises(ValueError):installer.checked('https://official.example/fixture','0'*64)
    def test_unknown_mode_cannot_start_listener(self):
        with patch.object(entry.sys,'argv',['entrypoint','other']),patch.object(entry.os,'execv') as execute:
            with self.assertRaises(ValueError):entry.main()
            execute.assert_not_called()
    def test_build_context_whitelist(self):
        patterns=(ROOT/'.dockerignore').read_text().splitlines()
        self.assertEqual(patterns[0],'*');self.assertNotIn('!.env',patterns)
        self.assertEqual(set(x[1:] for x in patterns if x.startswith('!')),{'Dockerfile','entrypoint.py','install_tools.py'})

if __name__=='__main__':unittest.main(verbosity=2)
