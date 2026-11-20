const c=require("./conteudo.js");let a=0,b=0,f=0,t=0,q=0,ks=[];
for(const x of c){if(x[0]=="h1"){a++;b=0;ks.push(a+" "+x[1])}else if(x[0]=="h2"){b++;ks.push(a+"."+b+" "+x[1])}else if(x[0]=="fig"){f++;ks.push("Figura "+f+" – "+x[4])}else if(x[0]=="tab"){if(x[1]=="Tabela"){t++;ks.push("Tabela "+t+" – "+x[2])}else{q++;ks.push("Quadro "+q+" – "+x[2])}}}
ks.push("REFERÊNCIAS");require("fs").writeFileSync("chaves.json",JSON.stringify(ks));
