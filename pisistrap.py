from lxml import etree

import os
import os.path
import urllib2
import sys
import zipfile

class PisiPackage:

	def __init__(self, name=None, rdeps=None, uri=None):
		self.name = name
		self.rdeps = rdeps
		self.uri = uri

class PisiIndex:

	def __init__(self, fileName):
		self.pIndex = open(fileName, "r")
		print "Parsing %s" % fileName

		tree = etree.parse(self.pIndex)
		root = tree.getroot()
		self.pkgTree = dict()
		for e in root:
			# grab name and dependencies
			name = None
			rdeps = list()
			uri = None
			for i in e:
				if i.tag == "Name":
					name = i.text
				if i.tag == "RuntimeDependencies":
					for dep in i:
						#if "pisi" in name:
							#print "%s depends on %s" % (name, dep.text)
						rdeps.append(dep.text)
				if i.tag == "PackageURI":
					uri = i.text
			self.pkgTree[name] = PisiPackage(name=name, rdeps=rdeps,uri=uri)
		self.pIndex.close()


	def get_package(self, name):
		return self.pkgTree[name]

	def compute_dependencies(self, name, depth=0):
		dependencyTree = list()
		package = self.get_package(name)

		dependencyTree.append(name)
		for dependency in package.rdeps:
			dependencyTree.append(dependency)
			
			dependencyTree.extend(self.compute_dependencies(dependency,depth=(depth+1)))
		return dependencyTree


class PisiDownloader:

	def __init__(self, index=None, repo=None, output_dir=None, base_system=None):
		self.output_dir = output_dir
		if (index is None):
			# We're being used to download the pisi-index.xml.xz
			return



		# Grab all dependencies of base system
		depTree = list()
		for pkg in base_system:
			depTree.extend(index.compute_dependencies(pkg))

		# clean them out
		rDepTree = list()
		for dep in depTree:
			if dep not in rDepTree:
				rDepTree.append(dep)
		depTree = None # restore some memory ^^

		if not os.path.exists(output_dir):
			print "%s does not exist. Creating it"
			os.mkdir(output_dir)


		# Down 'em all!
		count = 0
		total = len(rDepTree)
		for package_name in rDepTree:
			count = count +1
			package = index.get_package(package_name)
			uri = "%s/%s" % (repo, package.uri)

			output_name = os.path.join(self.output_dir, package.uri)
			if not os.path.exists(output_name):
				print "Downloading package %s [%d of %d]" % (package_name, count, total)
				try:
					self.download_package(uri)
				except Exception, ex:
					print "Failed to download %s" % package_name
					print ex
					sys.exit(-1)
			else:
				print "Skipping %s, already downloaded [%d of %d]" % (package_name, count, total)

	def download_package(self, url):
		file_name = url.split('/')[-1]
		output = os.path.join(self.output_dir, file_name)
		u = urllib2.urlopen(url)
		f = open(output, 'wb')
		meta = u.info()
		file_size = int(meta.getheaders("Content-Length")[0])

		file_size_dl = 0
		block_sz = 8192
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break

			file_size_dl += len(buffer)
			f.write(buffer)
			status = r" [%3.2f%%] %s/%s %s" % (file_size_dl * 100. / file_size, self.sizeof_fmt(file_size_dl), self.sizeof_fmt(file_size), file_name)
			status = status + chr(8)*(len(status)+1)
			print status,

		print "\n"
		f.close()

	def sizeof_fmt(self, num):
		for x in ['bytes','KB','MB','GB']:
			if num < 1024.0:
				return "%3.1f%s" % (num, x)
			num /= 1024.0
		return "%3.1f%s" % (num, 'TB')

class PisiUtil:

	def extract(self, pkgName, output_dir):

		if not os.path.exists(output_dir):
			print "Creating output directory"
			os.mkdir(output_dir)

		try:
			pisi = zipfile.ZipFile(pkgName)

			installFile = pisi.getinfo("install.tar.xz")

			pisi.extract(installFile, output_dir)
			pisi.close()

			dire = os.getcwd()
			os.chdir(output_dir)
			cmd = "sudo tar xvf install.tar.xz --preserve-permissions --overwrite --atime-preserve"
			os.system(cmd)
			os.chdir(dire)

			# kill the install.tar.xz
			removal = os.path.join(output_dir, "install.tar.xz")
			os.remove(removal)
		except Exception, ex:
			print ex
			sys.exit(-1)

	def make_nodes(self, output_dir):
		if not os.path.exists(output_dir):
			print "Aborting! Invalid work directory"
			sys.exit(-1)

		cwd = os.getcwd()
		os.chdir(output_dir)
		os.system("sudo mknod dev/console c 5 1")
		os.system("sudo mknod dev/null c 1 3")
		os.system("sudo mknod dev/random c 1 8")
		os.system("sudo mknod dev/urandom c 1 9")
		os.chdir(cwd)

	def create_base(self, output_dir):
		os.system("sudo cp -Rv base/* %s/etc/" % output_dir)

if __name__ == "__main__":
	baseURI = "http://paketler.pardus-linux.org/pardus/2012/testing/x86_64"
	if not os.path.exists("pisi-index.xml"):

		pkgIndex = "%s/%s" % (baseURI, "pisi-index.xml.xz")
		print "Attempting to download latest package index from %s" % pkgIndex
		downloader = PisiDownloader(index=None, output_dir=os.getcwd())

		downloader.download_package(pkgIndex)
		os.system("unxz pisi-index.xml.xz")
		print "Run this script again to build the base system"
		sys.exit(0)

	index = PisiIndex("pisi-index.xml")

	baseSystemMin = ("bash", "bash-completion", "nano", "libuser", "binutils", "pisi", "comar", "glibc", "glibc-locales-en", "glib2", "grep", "sed", "libcap", "file", "dbus-python") # Minimal system


	baseSystemDev = ("bash", "bash-completion", "nano", "libuser", "binutils", "pisi", "comar", "glibc", "glibc-locales-en", "glib2", "grep", "sed", "libcap", "file", "dbus-python", "gcc", "make", "automake") # Builder system


	# should have a start() method :p
	downloader = PisiDownloader(index=index, repo=baseURI, output_dir="cache", base_system=baseSystemDev)


	utils = PisiUtil()

	for name in os.listdir("cache"):
		fullName = os.path.join("cache", name)
		utils.extract(fullName, "work")

	print "Creating device nodes for base system"
	utils.make_nodes("work")
	print "Copying base system across"
	utils.create_base("work")

	# copy all the packages into the chroot
	os.system("cp cache/*.pisi work/.")


