import json
import threading
import unittest
from unittest.mock import Mock, patch

from jarvis.agent import Agent
from jarvis.computer import valid_action
from jarvis.desktop import DesktopAPI


class Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.payload).encode()


class AgentTests(unittest.TestCase):
    def test_natural_conversation_with_openai(self):
        agent=Agent(); agent.key='test'; agent.provider='openai'
        data={'choices':[{'message':{'content':'İyiyim, teşekkürler. Sen nasılsın?'}}]}
        with patch('jarvis.agent.urllib.request.urlopen', return_value=Response(data)) as request:
            answer=agent.ask('Nasılsın?')
        self.assertIn('İyiyim',answer['text'])
        self.assertEqual(answer['actions'],[])
        body=json.loads(request.call_args.args[0].data)
        self.assertEqual(body['messages'][-1]['content'],'Nasılsın?')

    def test_tool_call_is_proposal_not_execution(self):
        agent=Agent(); agent.key='test'; agent.provider='openai'
        call={'function':{'name':'type_text','arguments':'{"text":"Merhaba dünya"}'}}
        data={'choices':[{'message':{'content':None,'tool_calls':[call]}}]}
        with patch('jarvis.agent.urllib.request.urlopen',return_value=Response(data)):
            answer=agent.ask('Metni yaz')
        self.assertEqual(answer['actions'][0]['name'],'type_text')

    def test_disallow_unbounded_action(self):
        with self.assertRaises(ValueError): valid_action('run_shell',{'command':'del *'})
        with self.assertRaises(ValueError): valid_action('type_text',{'text':'dir\n'} )
        with self.assertRaises(ValueError): valid_action('write_document',{'title':'../secret','text':'x'})

    def test_confirmation_is_required_and_one_time(self):
        api=DesktopAPI.__new__(DesktopAPI)
        api.agent=Mock()
        api.agent.selected_provider.return_value='openai'
        api.agent.ask.return_value={'text':'Yazmayı öneriyorum.',
                       'actions':[valid_action('type_text',{'text':'Deneme'})]}
        api.agent.history=[]
        api.voice=Mock(); api.assistant=Mock(); api.pending={}; api._lock=threading.Lock()
        with patch('jarvis.desktop.perform',return_value='Yazıldı.') as perform:
            result=api.command('Deneme yaz')
            perform.assert_not_called()
            self.assertIn('proposal',result)
            token=result['proposal']['id']
            api.execute_pending(token)
            perform.assert_called_once()
            self.assertFalse(api.execute_pending(token)['ok'])


if __name__=='__main__': unittest.main()
