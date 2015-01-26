import json
m={
		'name': 'lamp',
		"suscribeto": [
		{

		}
		],
		"publishto": [
		{
			"powerlamp": "0",
			"assignlamptopic": "",
			"assignlampmsgon": "",
			"assignlampmsgoff": ""
	}
	]
	}
n={
		'name': 'lamp',
		"suscribeto": [
		{

		}
		],
		"publishto": [
		{
			"powerlamp": "0",
			"assignlamptopic": "",
			"assignlampmsgon": "",
			"assignlampmsgoff": ""
	}
	]
	}

def jsonact(jsondir,value,metajson):
	if metajson[jsondir]['action'] == 'print':
		print "valor:"+str(value)

def jsoncompare(cmprto,becmpr,currentDir,metacmpr):
	try:
		k=cmprto.keys()
		x=0
		while len(k) > x:		
			subdir=jsoncompare(cmprto[k[x]],becmpr[k[x]],'/'+str(currentDir)+str(k[x]),metacmpr)
			if subdir=="nell":
				#print str(k[x])+" : "+str(cmprto[k[x]])+" == "+str(k[x])+" : "+str(becmpr[k[x]])
				if cmprto[k[x]] is not becmpr[k[x]]:
					jsonact(currentDir+'/'+str(k[x]),becmpr[k[x]],metacmpr)
			x+=1
	except:
		return "nell"
		
o={'a':1}
w = {'a':{'a1':4,'a2':5},'b':2,'c':3,'d':4}
c = {'a':{'a1':2,'a2':5},'b':2,'c':3,'d':4}
result = {
  1: lambda x: x * 1,
  2: lambda x: x * 2,
  3: lambda x: x * 3
}

mw={'/a/a1':{'action':'print'},'type':'mqtt'}
z = dict(a=2, b=2,c=3, d=4)
#shared_items = set(w.items()) & set(z.items())
#print shared_items
#print x[None][0].keys()

print result[1](2)
print result[2](2)
print result[3](2)
print result[4](2)

#jsoncompare(w,c,'',mw)


#try:
#	print x['name'][0].keys()
#except:
#	print "no se pudo"
