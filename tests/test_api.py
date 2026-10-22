import importlib.util, json, os, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path

MODULE_PATH=Path(__file__).resolve().parents[1]/'server.py'
spec=importlib.util.spec_from_file_location('nagrivanta_server',MODULE_PATH)
app=importlib.util.module_from_spec(spec); spec.loader.exec_module(app)

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        app.DB_PATH=Path(cls.temp.name)/'test.sqlite3'
        app.init_db()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(2); cls.temp.cleanup()
    def request(self,path,body=None,method='GET'):
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(self.base+path,data=data,method=method,headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req) as res:return res.status,json.loads(res.read())
        except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
    def test_seed_has_duplicate_and_workflow_stages(self):
        _,d=self.request('/api/reports'); reports=d['reports']; ids={r['id']:r for r in reports}
        self.assertTrue(ids['NG-DEMO-102']['master_id'])
        self.assertEqual(ids['NG-DEMO-103']['status'],'assigned')
        self.assertEqual(ids['NG-DEMO-104']['status'],'repair_submitted')
    def test_full_report_to_verified_closure(self):
        payload={'title':'Broken road near library','category':'Road damage','description':'A broken road surface is near the public library entrance and can cause a fall.','area':'Ward Test','address':'Library Lane','before_photo':app.sample_photo('test')}
        code,d=self.request('/api/reports',payload,'POST'); self.assertEqual(code,201); rid=d['report']['id']
        code,_=self.request('/api/reports/'+rid,{'action':'assign','actor':'Municipal','department':'Roads','crew':'Crew A'},'POST'); self.assertEqual(code,200)
        code,_=self.request('/api/reports/'+rid,{'action':'repair','actor':'Crew','after_photo':app.sample_photo('after'),'repair_note':'Filled and levelled the damaged patch.'},'POST'); self.assertEqual(code,200)
        code,d=self.request('/api/reports/'+rid,{'action':'verify','actor':'Inspector','approved':True,'checks':['1','2','3','4'],'notes':'Checked photos and location.'},'POST'); self.assertEqual(code,400)
        code,d=self.request('/api/reports/'+rid,{'action':'verify','actor':'Inspector','approved':True,'checks':['1','2','3','4','5'],'notes':'Checked photos and location; work appears complete.'},'POST'); self.assertEqual(code,200); self.assertEqual(d['report']['status'],'verified')
    def test_duplicate_links_source_without_replacing(self):
        photo=app.sample_photo('dup')
        base={'title':'Pothole school entrance','category':'Road damage','description':'Large pothole at the school entrance causes traffic danger near the crossing.','area':'Ward 97','address':'New Test Avenue, near library','before_photo':photo}
        _,one=self.request('/api/reports',base,'POST')
        two={**base,'title':'Another pothole at school entrance'}
        _,d=self.request('/api/reports',two,'POST')
        self.assertEqual(d['duplicate']['master_id'],one['report']['id'])
        _,all_data=self.request('/api/reports')
        self.assertTrue(any(x['id']==one['report']['id'] for x in all_data['reports']))
        self.assertTrue(any(x['id']==d['report']['id'] for x in all_data['reports']))
    def test_assignment_requires_department_and_crew(self):
        code,d=self.request('/api/reports/NG-DEMO-101',{'action':'assign','actor':'Municipal','department':'','crew':''},'POST')
        self.assertEqual(code,400); self.assertIn('department',d['error'].lower())

if __name__=='__main__': unittest.main()
