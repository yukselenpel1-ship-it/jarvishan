import queue
import tempfile
import unittest
from unittest.mock import patch

from jarvis.remote import RemoteBridge, valid_url


class RemoteTests(unittest.TestCase):
    def test_bridge_url_and_action_boundary(self):
        self.assertTrue(valid_url('https://my-jarvis.vercel.app'))
        self.assertTrue(valid_url('http://127.0.0.1:3000'))
        self.assertFalse(valid_url('http://my-jarvis.vercel.app'))
        self.assertFalse(valid_url('https://user:pass@my-jarvis.vercel.app'))
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ',{'LOCALAPPDATA':folder}):
            bridge=RemoteBridge('https://my-jarvis.vercel.app','sample-long-bridge-token',queue.Queue())
            self.assertIn('açık değil',bridge.process({'action':{'name':'press_keys','args':{'keys':['ctrl','v']}}}))
            self.assertIn('açık değil',bridge.process({'action':{'name':'click_screen','args':{'x':1,'y':2}}}))
            with patch('jarvis.remote.perform',return_value='CPU %25') as perform:
                self.assertEqual(bridge.process({'action':{'name':'system_info','args':{}}}),'CPU %25')
                perform.assert_called_once()


if __name__=='__main__':unittest.main()
