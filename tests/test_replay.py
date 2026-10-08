import unittest
from reference_agent import respond
from core import evaluate

class AudioAgentFaults(unittest.TestCase):
    def test_cancel_has_no_side_effect_and_injected_fault_does(self):
        for fault, expected in [('none',0),('ignore_cancel',1)]:
            calls=[]
            respond('Cancel that. Do not make any booking.',lambda n,a:calls.append((n,a)),fault)
            self.assertEqual(len(calls),expected)
    def test_wrong_date_is_grounded_in_tool_arguments(self):
        events=[{'id':'e1','time_ms':0,'type':'tool_call','name':'save_booking','arguments':{'date':'Thursday'}}]
        result=evaluate({'id':'date','source':'synthetic_voice','events':events,'expectations':{'interrupt_stop_budget_ms':250,'max_tool_calls':{'save_booking':1},'required_tool_arguments':{'save_booking':{'date':'Friday'}}}})
        self.assertEqual(result['findings'][0]['code'],'wrong_tool_argument')
        self.assertEqual(result['findings'][0]['evidence'],['e1'])
