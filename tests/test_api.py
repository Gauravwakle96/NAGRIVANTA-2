import base64, importlib.util, json, os, sqlite3, tempfile, threading, unittest, urllib.request, urllib.error
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
    def test_catalog_includes_heritage_and_multiple_departments(self):
        code,d=self.request('/api/catalog')
        self.assertEqual(code,200)
        groups={item['name']:item for item in d['categories']}
        self.assertIn('Heritage and Historical Sites',groups)
        self.assertGreaterEqual(len(d['departments']),10)
        self.assertTrue(any('graffiti' in item['name'].lower()
                            for item in groups['Heritage and Historical Sites']['subcategories']))
    def test_heritage_report_gets_competent_authority_recommendation(self):
        payload={'title':'Graffiti on old stone gate','category':'Heritage and Historical Sites',
                 'subcategory':'Monument vandalism, graffiti or defacement',
                 'description':'Graffiti is visible on a historic stone gate and needs an authorized assessment.',
                 'area':'Demo Ward','address':'Synthetic heritage location',
                 'before_photo':app.sample_photo('heritage test')}
        code,d=self.request('/api/reports',payload,'POST')
        self.assertEqual(code,201)
        self.assertEqual(d['report']['category_group'],'Heritage and Historical Sites')
        self.assertIn('Heritage Cell',d['recommendation']['department'])
        self.assertEqual(d['report']['status'],'submitted')
    def test_water_and_waste_routes_are_configured(self):
        examples=[
            ('Water Supply and Drainage','Blocked drain','Drainage'),
            ('Solid Waste Management and Sanitation','Overflowing public bin','Solid Waste Management'),
        ]
        for category,subcategory,department in examples:
            payload={'title':'Issue needing municipal attention','category':category,'subcategory':subcategory,
                     'description':'A public issue needs review by the responsible department.',
                     'area':'Demo Ward','address':f'Synthetic {subcategory} location',
                     'before_photo':app.sample_photo('routing test')}
            code,d=self.request('/api/reports',payload,'POST')
            self.assertEqual(code,201)
            self.assertEqual(d['recommendation']['department'],department)
    def test_rule_based_triage_discloses_method(self):
        code,d=self.request('/api/triage',{'description':'Garbage is overflowing from a public bin.'},'POST')
        self.assertEqual(code,200)
        result=d['recommendation']
        self.assertEqual(result['method'],'rule-based')
        self.assertEqual(result['category'],'Solid Waste Management and Sanitation')
        self.assertIn('human review',result['explanation'].lower())
    def test_additive_migration_preserves_legacy_report_id_and_category(self):
        old_path=app.DB_PATH
        with tempfile.TemporaryDirectory() as folder:
            legacy_path=Path(folder)/'legacy.sqlite3'
            db=sqlite3.connect(legacy_path)
            db.execute('''CREATE TABLE reports (
              id TEXT PRIMARY KEY, category TEXT NOT NULL, status TEXT NOT NULL, department TEXT
            )''')
            db.execute("INSERT INTO reports(id,category,status,department) VALUES (?,?,?,?)",
                       ('NG-LEGACY-123','Road damage','submitted',None))
            db.commit(); db.close()
            try:
                app.DB_PATH=legacy_path
                app.init_db()
                db=sqlite3.connect(legacy_path)
                row=db.execute("SELECT id,category,subcategory,suggested_department FROM reports WHERE id=?",
                               ('NG-LEGACY-123',)).fetchone()
                db.close()
                self.assertEqual(row[0],'NG-LEGACY-123')
                self.assertEqual(row[1],'Road damage')
                self.assertTrue(row[2])
                self.assertEqual(row[3],'Roads and Engineering')
            finally:
                app.DB_PATH=old_path
    def test_demo_reset_is_disabled_unless_explicitly_enabled(self):
        previous=os.environ.pop('NAGRIVANTA_DEMO_RESET',None)
        try:
            code,d=self.request('/api/demo/reset',{},'POST')
            self.assertEqual(code,403)
            self.assertIn('disabled',d['error'].lower())
        finally:
            if previous is not None: os.environ['NAGRIVANTA_DEMO_RESET']=previous
    def test_unsafe_svg_upload_is_rejected(self):
        unsafe='data:image/svg+xml;base64,'+base64.b64encode(b'<svg onload="alert(1)"></svg>').decode()
        payload={'title':'Test upload','category':'Road damage','description':'A sufficiently detailed report description for validation.',
                 'area':'Ward Test','address':'Test Lane','before_photo':unsafe}
        code,d=self.request('/api/reports',payload,'POST')
        self.assertEqual(code,400)
        self.assertIn('unsupported SVG',d['error'])
    def test_non_string_category_is_rejected_cleanly(self):
        payload={'title':'Test category','category':['Road damage'],'subcategory':'',
                 'description':'A sufficiently detailed report description for validation.',
                 'area':'Ward Test','address':'Test Lane','before_photo':app.sample_photo('test')}
        code,d=self.request('/api/reports',payload,'POST')
        self.assertEqual(code,400)
        self.assertIn('category',d['error'].lower())

if __name__=='__main__': unittest.main()
