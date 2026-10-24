import subprocess,json,re,os
HERE=os.path.dirname(os.path.abspath(__file__)); SUB=os.path.join(HERE,"..")
n=int(re.search(r"Pages:\s+(\d+)",subprocess.run(["pdfinfo",SUB+"/OS_Tutor_RAG_Report.pdf"],capture_output=True,text=True).stdout).group(1))
heads={"Introduction":"1. Introduction","Literature Review":"2. Literature Review","Problem Statement":"3. Problem Statement","Objectives":"4. Objectives","Methodology":"5. Methodology","Results and Discussion":"6. Results and Discussion","Conclusion":"7. Conclusion","Limitations":"8. Limitations","Future Work":"9. Future Work","References":"10. References",
"5.1  System overview":"5.1 System overview","5.2  Ingestion and chunking":"5.2 Ingestion and chunking","5.3  Retrieval and context expansion":"5.3 Retrieval and context expansion","5.4  Generation: the prompts":"5.4 Generation: the prompts","5.5  The tutoring layer":"5.5 The tutoring layer","5.6  Evaluation protocol":"5.6 Evaluation protocol","5.7  Research protocol: RCR":"5.7 Research protocol","6.1  Retrieval and defects":"6.1 Retrieval and defects","6.2  Prompt results":"6.2 Prompt results","6.3  Noise floor":"6.3 Noise floor","6.4  The tutoring layer":"6.4 The tutoring layer","6.5  Research track: RCR results":"6.5 Research track"}
res={}
for p in range(3,n+1):
    t=subprocess.run(["pdftotext","-f",str(p),"-l",str(p),"-layout",SUB+"/OS_Tutor_RAG_Report.pdf","-"],capture_output=True,text=True).stdout
    for k,h in heads.items():
        if k not in res and re.search(r"^\s*"+re.escape(h),t,re.M): res[k]=str(p)
print(res); json.dump(res,open(HERE+"/toc_pages.json","w"))
