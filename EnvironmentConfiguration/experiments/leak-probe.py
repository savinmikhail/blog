import pathlib,subprocess,json,os
p=pathlib.Path(__file__).resolve().parent
(p/'dummy-secret.txt').write_text('DEMO_NOT_A_REAL_SECRET_12345\n')
(p/'leak.yaml').write_text('services:\n  app:\n    image: busybox:1.37\n    environment:\n      API_KEY: ${DEMO_API_KEY}\n    secrets:\n      - demo\nsecrets:\n  demo:\n    file: ./dummy-secret.txt\n')
r=subprocess.run(['docker','compose','-f','leak.yaml','config','--format','json'],cwd=p,env={**os.environ,'DEMO_API_KEY':'DEMO_NOT_A_REAL_SECRET_12345'},text=True,capture_output=True)
j=json.loads(r.stdout)
results={'config_exit':r.returncode,'environment_value_in_config':j['services']['app']['environment']['API_KEY'],'secret_file_content_in_config': 'DEMO_NOT_A_REAL_SECRET_12345' in json.dumps(j.get('secrets',{})), 'secret_definition': j.get('secrets',{})}
(p/'dummy-secret.txt').chmod(0o600)
results['chmod_600_same_user_can_read']= (p/'dummy-secret.txt').read_text().strip()=='DEMO_NOT_A_REAL_SECRET_12345'
(p/'leak-results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
