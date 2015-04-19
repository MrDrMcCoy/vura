import cherrypy, string, shutil, os, os.path, glob, sys, thread, threading, urllib, concurrent, futures, socket, re, subprocess, distutils, mimetypes
from concurrent.futures.thread import ThreadPoolExecutor
from distutils import spawn

# Get IP address
def getip():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('8.8.8.8', 0)) 
		local_ip_address = s.getsockname()[0]
		return local_ip_address
	except:
		cherrypy.log('| ERROR | Unable determine IP address')
		return "localhost"

# Create thread for downloader
downloadThread = threading.Thread()

# Create progress counter for downloader
progress = 0

# Check for genisoimage
genisoimage = distutils.spawn.find_executable('genisoimage')
if os.path.exists(genisoimage):
    canimakeaniso = "True"
else:
    canimakeaniso = "False"

def get_folder_size(folder_path):
# Because I don't want to depend on a system call
    try:
        folder_size = 0
        for (path, dirs, files) in os.walk(folder_path):
            for file in files:
                filename = os.path.join(path, file)
                folder_size += os.path.getsize(filename)
        return str(folder_size/1024/1024) + 'MB'
    except:
        cherrypy.log('| ERROR | Unable to get folder size for '+name)

# Function to write repo state file
def statewriter(name, message):
    try:
        with open('repo/'+name+'/state','w') as state:
            state.write(message)
        state.close()
    except:
        cherrypy.log('| ERROR | Unable to write state file for '+name)

# Download individual file and increment progress counter
def fetch(name, url, destination, queuesize):
    global progress
    try:
        #cherrypy.log('| INFO | Downloading '+destination)
        urllib.urlretrieve(url, destination)
    except:
        cherrypy.log('| ERROR | Unable to download '+destination)
    progress += 1
    statewriter(name, 'Downloaded '+str(progress)+'/'+str(queuesize))

# Queue multiple downloads and reset progress counter
def downloader(queue, name):
    queuesize = len(queue)
    global progress
    progress = 0
    cherrypy.log("| INFO | Downloading "+str(queuesize)+" files for "+name)
    with ThreadPoolExecutor(max_workers=8) as executor:
        for url, destination in zip(queue.keys(), queue.values()):
            executor.submit(fetch, name, url, destination, queuesize)
    cherrypy.log("| INFO | Finished downloading "+str(queuesize)+" files for "+name)

# Populate new repositories
def repoman(name):
    try:
        cherrypy.log("| INFO | Initializing repo: "+name)
        statewriter(name, 'Initializing')
        #read base url from file
        baseurl=open('repo/'+name+'/url').read()
        #build list of manifest files to download
        manifest={}
        manifest[baseurl+'/manifest/manifest-latest.xml']='repo/'+name+'/manifest/manifest-latest.xml'
        manifest[baseurl+'/manifest/manifest-latest.xml.sha256']='repo/'+name+'/manifest/manifest-latest.xml.sha256'
        manifest[baseurl+'/manifest/manifest-latest.xml.sig']='repo/'+name+'/manifest/manifest-latest.xml.sig'
        manifest[baseurl+'/manifest/manifest-repo.xml']='repo/'+name+'/manifest/manifest-repo.xml'
    except:
        cherrypy.log("| ERROR | Initializing repo failed for "+name)
    #download manifest files
    downloader(manifest, name)
    try:
        cherrypy.log("| INFO | Building download list for "+name)
        #read manifest file
        manifest_file = open('repo/'+name+'/manifest/manifest-latest.xml')
        #create dictionary of packages to download
        package_pool={}
        for line in manifest_file:
            if re.match('package-pool', line):
                pkg = line.rstrip()
                package_pool[baseurl+'/'+pkg]='repo/'+name+'/'+pkg
    except:
        cherrypy.log("| ERROR | Building download list failed for "+name)
    #download repo packages
    downloader(package_pool, name)
    statewriter(name, 'Ready')
    #generate update.iso, if possible
    if canimakeaniso is "True":
        try:
            cherrypy.log("| INFO | Building ISO for "+name)
            os.popen(genisoimage+' -f -r -U -J -joliet-long -o update.iso.tmp repo/'+name).close()
            shutil.move('update.iso.tmp','repo/'+name+'/update.iso')
        except:
            cherrypy.log("| ERROR | Building ISO failed for "+name)
    else:
        cherrypy.log("| WARN | genisoimage not installed, skipping ISO creation for "+name)

# Initialize new repo
def createrepo(name, url):
    global downloadThread
    if not os.path.exists('repo/'+name):
        cherrypy.log("| INFO | Creating repo: "+name)
        os.makedirs('repo/'+name)
        os.makedirs('repo/'+name+'/manifest')
        os.makedirs('repo/'+name+'/package-pool')
    else:
        cherrypy.log("| WARN | Unable to create repo directory for "+name+", skipping")
    statewriter(name, 'Starting')
    #save repo source URL to file
    try:
        with open('repo/'+name+'/url','w') as urlfile:
            urlfile.write(url)
        urlfile.close()
    except:
        cherrypy.log('| ERROR | Unable to write URL file for '+name)
    #begin downloading
    if downloadThread.isAlive():
        cherrypy.log("| ERROR | Download already in progress! Skipping "+name)
    else:
        cherrypy.log("| INFO | Preparing Download")
        downloadThread = threading.Thread(target=repoman, args=[name])
        downloadThread.start()
    return """<META http-equiv="refresh" content="0;URL=/">"""

def deleterepo(name):
    try:
        cherrypy.log("| INFO | Deleting repo: "+name)
        shutil.rmtree('repo/'+name)
    except:
        cherrypy.log("| ERROR | Deleting repo failed for "+name)
    return """<META http-equiv="refresh" content="0;URL=/">"""

class ui(object):
    #display web UI
    @cherrypy.expose
    def index(self):
        return file('index.html')

    #List repos and stats. Formatted in JSON for DataTables
    @cherrypy.expose
    def list(self, _):
        try:
            #cherrypy.log('| INFO | Listing repos')
            repocount = len(os.listdir('repo'))
            jsondata='{"data":['
            for reponame in os.listdir('repo'):
                if os.path.exists('repo/'+reponame+'/state'):
                    status = open('repo/'+reponame+'/state').read()
                else:
                    status = 'Error'
                    cherrypy.log('| ERROR | Unable to read repo state file for '+reponame)
                address = 'http://'+getip()+'/repo/'+reponame
                if os.path.exists('repo/'+reponame+'/update.iso'):
                    isofile = '<a href=\\"'+'http://'+getip()+'/repo/'+reponame+'/update.iso\\">Download ISO</a>'
                elif canimakeaniso is "False":
                    isofile = 'genisoimage not installed'
                elif os.path.exists('update.iso.tmp'):
                    isofile = 'Not ready'
                elif 'ownload' in status:
                    isofile = 'Not ready'
                else:
                    isofile = 'Unavailable'
                reposize = get_folder_size('repo/'+reponame)
                deletebutton = '<a href=\\"'+'http://'+getip()+'/delete?name='+reponame+'\\"><button type=\\"button\\">delete</button></a>'
                jsondata += '["'+reponame+'","'+address+'","'+isofile+'","'+reposize+'","'+status+'","'+deletebutton+'"]'
                repocount -= 1
                if repocount > 0:
                    jsondata += ','
            jsondata += ']}'
            return jsondata
        except:
            cherrypy.log('| ERROR | Listing repos failed')

    #receive creation request from web form and kick off thread
    @cherrypy.expose
    def create(self, create, name, url):
        with ThreadPoolExecutor(max_workers=1) as executor:
        	future = executor.submit(createrepo, name, url)
        return """<META http-equiv="refresh" content="0;URL=/">"""

    #delete repository
    @cherrypy.expose
    def delete(self, name):
        with ThreadPoolExecutor(max_workers=1) as executor:
        	future = executor.submit(deleterepo, name)
        return """<META http-equiv="refresh" content="0;URL=/">"""

conf = {
	'global': {
	    'log.access_file': "vura-access.log",
	    'log.error_file': "vura-actions.log",
	    'server.socket_host': '0.0.0.0',
	    'server.socket_port': 80
	    },
    '/': {
    	'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
 	'/repo': {
    	'tools.staticdir.on': True,
    	'tools.staticdir.dir': 'repo'
	}
}
cherrypy.quickstart(ui(), '/', conf)
