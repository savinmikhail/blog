import pathlib,subprocess,json,os
p=pathlib.Path(__file__).resolve().parent
(p/'sample.env').write_text('BASE=alpha\nEXPANDED=${BASE}/data\nLITERAL=cost$$cash\n')
(p/'Makefile').write_text('include sample.env\nexport\nprobe:\n\t@python3 -c \'import os,json; print(json.dumps({k:os.getenv(k) for k in ["BASE","EXPANDED","LITERAL"]}))\'\n')
(p/'compose.yaml').write_text('services:\n  app:\n    image: busybox:1.37\n    environment:\n      BASE: ${BASE}\n      EXPANDED: ${EXPANDED}\n      LITERAL: ${LITERAL}\n')
results={}
commands={'node':['node','--env-file=sample.env','-e','console.log(JSON.stringify(Object.fromEntries(["BASE","EXPANDED","LITERAL"].map(k=>[k,process.env[k]]))))'], 'bash':['bash','-c','set -a; source sample.env; python3 -c \'import os,json; print(json.dumps({k:os.getenv(k) for k in ["BASE","EXPANDED","LITERAL"]}))\''], 'make':['make','--no-print-directory','probe'],'compose':['docker','compose','--env-file','sample.env','config','--format','json']}
env={k:v for k,v in os.environ.items() if k not in ['BASE','EXPANDED','LITERAL','COMPOSE_FILE','COMPOSE_ENV_FILES','COMPOSE_PROJECT_NAME','VALUE','ONLY_RUNTIME']}
for name,cmd in commands.items():
 r=subprocess.run(cmd,cwd=p,env=env,text=True,capture_output=True)
 results[name]={'exit':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
 if name=='compose' and r.returncode==0: results[name]['stdout']=json.loads(r.stdout)['services']['app']['environment']
(p/'base.env').write_text('VALUE=base\n')
(p/'local.env').write_text('VALUE=local\n')
(p/'runtime.env').write_text('VALUE=runtime-file\nONLY_RUNTIME=present\n')
(p/'precedence.yaml').write_text('services:\n  app:\n    image: busybox:1.37\n    env_file: runtime.env\n    environment:\n      VALUE: ${VALUE}\n')
for shell in [False,True]:
 e=env.copy()
 if shell:e['VALUE']='shell'
 r=subprocess.run(['docker','compose','-f','precedence.yaml','--env-file','base.env','--env-file','local.env','config','--format','json'],cwd=p,env=e,text=True,capture_output=True)
 results['precedence_shell_'+str(shell)]={'exit':r.returncode,'environment':json.loads(r.stdout)['services']['app']['environment'] if r.returncode==0 else r.stderr}
results['versions']={name:subprocess.run(cmd,text=True,capture_output=True).stdout.strip() for name,cmd in {'node':['node','--version'],'bash':['bash','--version'],'make':['make','--version'],'compose':['docker','compose','version']}.items()}
(p/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
