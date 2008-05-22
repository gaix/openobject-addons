import os
import time
from tarfile import filemode

import pooler
import netsvc
import posix
from service import security

class abstracted_fs:
	"""A class used to interact with the file system, providing a high
	level, cross-platform interface compatible with both Windows and
	UNIX style filesystems.

	It provides some utility methods and some wraps around operations
	involved in file creation and file system operations like moving
	files or removing directories.

	Instance attributes:
	 - (str) root: the user home directory.
	 - (str) cwd: the current working directory.
	 - (str) rnfr: source file to be renamed.
	"""

	# Ok
	def db_list(self):
		s = netsvc.LocalService('db')
		result = s.list()
		self.db_name_list=[]
		for db_name in result:
			db = pooler.get_db_only(db_name)
			cr = db.cursor()
			cr.execute("select id from ir_module_module where name like 'document%' and state='installed' ")
			res=cr.fetchone()
			if res and len(res):
				self.db_name_list.append(db_name)
			cr.close()
		return self.db_name_list

	# Ok
	def __init__(self):
		self.root = None
		self.cwd = '/'
		self.rnfr = None

	# --- Pathname / conversion utilities

	# Ok
	def ftpnorm(self, ftppath):
		"""Normalize a "virtual" ftp pathname (tipically the raw string
		coming from client) depending on the current working directory.

		Example (having "/foo" as current working directory):
		'x' -> '/foo/x'

		Note: directory separators are system independent ("/").
		Pathname returned is always absolutized.
		"""
		if os.path.isabs(ftppath):
			p = os.path.normpath(ftppath)
		else:
			p = os.path.normpath(os.path.join(self.cwd, ftppath))
		# normalize string in a standard web-path notation having '/'
		# as separator.
		p = p.replace("\\", "/")
		# os.path.normpath supports UNC paths (e.g. "//a/b/c") but we
		# don't need them.  In case we get an UNC path we collapse
		# redundant separators appearing at the beginning of the string
		while p[:2] == '//':
			p = p[1:]
		# Anti path traversal: don't trust user input, in the event
		# that self.cwd is not absolute, return "/" as a safety measure.
		# This is for extra protection, maybe not really necessary.
		if not os.path.isabs(p):
			p = "/"
		return p

	# Ok
	def ftp2fs(self, path_orig):
		path = os.path.join(self.cwd, path_orig)
		print 'FTP2FS', path, self.cwd, path
		if path and path=='/':
			return None
		cr, uid, pool, path2 = self.get_cr(path)
		res = pool.get('document.directory').get_object(cr, uid, path2[:])
		if not res:
			raise OSError(2, 'Not such file or directory.')
		return res

	# Ok
	def fs2ftp(self, node):
		res = node and ('/' + node.cr.dbname + '/' + node.path) or '/'
		print 'FS2FTP', node, res

		return res

	# Ok
	def validpath(self, path):
		"""Check whether the path belongs to user's home directory.
		Expected argument is a "real" filesystem pathname.

		If path is a symbolic link it is resolved to check its real
		destination.

		Pathnames escaping from user's root directory are considered
		not valid.
		"""
		return path and True or False

	# --- Wrapper methods around open() and tempfile.mkstemp

	def open(self, filename, mode):
		"""Open a file returning its handler."""
		raise 'Not Yet Implemented'
		return open(filename, mode)

	def mkstemp(self, suffix='', prefix='', dir=None, mode='wb'):
		"""A wrap around tempfile.mkstemp creating a file with a unique
		name.  Unlike mkstemp it returns an object with a file-like
		interface.
		"""
		raise 'Not Yet Implemented'
		class FileWrapper:
			def __init__(self, fd, name):
				self.file = fd
				self.name = name
			def __getattr__(self, attr):
				return getattr(self.file, attr)

		text = not 'b' in mode
		# max number of tries to find out a unique file name
		tempfile.TMP_MAX = 50
		fd, name = tempfile.mkstemp(suffix, prefix, dir, text=text)
		file = os.fdopen(fd, mode)
		return FileWrapper(file, name)

	# Ok
	def chdir(self, path):
		self.cwd = self.fs2ftp(path)

	# Ok
	def mkdir(self, node, basename):
		"""Create the specified directory."""
		if not node:
			raise OSError(1, 'Operation not permited.')
		try:
			object2=node and node.object2 or False
			object=node and node.object or False
			cr = node.cr
			uid = node.uid
			pool = pooler.get_pool(cr.dbname)
			if node.object and (node.object.type=='ressource') and not node.object2:
				raise OSError(1, 'Operation not permited.')
			pool.get('document.directory').create(cr, uid, {
				'name': basename,
				'parent_id': object and object.id or False,
				'ressource_type_id': object and object.ressource_type_id.id or False,
				'ressource_id': object2 and object2.id or False
			})
			cr.commit()
			cr.close()
		except:
			raise OSError(1, 'Operation not permited.')


	# Ok
	def get_cr(self, path):
		dbname = path.split('/')[1]
		try:
			db,pool = pooler.get_db_and_pool(dbname)
		except:
			raise OSError(1, 'Operation not permited.')
		cr = db.cursor()
		uri2 = filter(None,path.split('/'))[1:]
		print 'GET CR', path, uri2
		uid = security.login(dbname, self.username, self.password)
		if not uid:
			raise OSError(1, 'Operation not permited.')
		return cr, uid, pool, uri2

	# Ok
	def listdir(self, path):
		"""List the content of a directory."""
		print 'LIST', path, path
		class false_node:
			object = None
			type = 'database'
			def __init__(self, db):
				self.path = '/'+db

		if path is None:
			result = []
			for db in self.db_list():
				result.append(false_node(db))
			return result
		return path.children()
#		result = []
#		for d in path.children():
#			print d.path
#			result.append( d.path.split('/')[-1] )
#		return result

	# Ok
	def rmdir(self, node):
		"""Remove the specified directory."""
		cr = node.cr
		uid = node.uid
		pool = pooler.get_pool(cr.dbname)
		object2=node and node.object2 or False
		object=node and node.object or False
		if object._table_name=='document.directory':
			if object.child_ids:
				raise OSError(39, 'Directory not empty.')
			if object.file_ids:
				raise OSError(39, 'Directory not empty.')
			res = pool.get('document.directory').unlink(cr, uid, [object.id])
		else:
			raise OSError(39, 'Directory not empty.')

		cr.commit()
		cr.close()

	# Ok
	def remove(self, node):
		"""Remove the specified file."""
		cr = node.cr
		uid = node.uid
		pool = pooler.get_pool(cr.dbname)
		object2=node and node.object2 or False
		object=node and node.object or False
		if not object:
			raise OSError(2, 'Not such file or directory.')
		if object._table_name=='ir.attachment':
			res = pool.get('ir.attachment').unlink(cr, uid, [object.id])
		else:
			raise OSError(1, 'Operation not permited.')
		cr.commit()
		cr.close()

	def rename(self, src, dst):
		"""Should process a read, a create and a remove"""
		raise 'Not Yet Implemented'

	def stat(self, node):
		return os.stat('/')
		print 'STAT', node
		r = list(os.stat('/'))
		if self.isfile(node):
			r[0] = 33188
		r[6] = self.getsize(node)
		r[7] = self.getmtime(node)
		r[8] =  self.getmtime(node)
		r[9] =  self.getmtime(node)
		return posix.stat_result(r)
	lstat = stat

	# --- Wrapper methods around os.path.*

	# Ok
	def isfile(self, node):
		if node and (node.type not in ('collection','database')):
			return True
		return False

	# Ok
	def islink(self, path):
		"""Return True if path is a symbolic link."""
		return False

	# Ok
	def isdir(self, node):
		"""Return True if path is a directory."""
		if node is None:
			return True
		if node and (node.type in ('collection','database')):
			return True
		return False

	# Ok
	def getsize(self, node):
		"""Return the size of the specified file in bytes."""
		result = 0L
		if node.type=='file':
			result = node.object.file_size or 0L
		return result

	# Ok
	def getmtime(self, node):
		"""Return the last modified time as a number of seconds since
		the epoch."""
		if node.object:
			dt = (node.object.write_date or node.object.create_date)[:19]
			result = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S'))
		else:
			result = time.mktime(time.localtime())
		return result

	# Ok
	def realpath(self, path):
		"""Return the canonical version of path eliminating any
		symbolic links encountered in the path (if they are
		supported by the operating system).
		"""
		return path

	# Ok
	def lexists(self, path):
		"""Return True if path refers to an existing path, including
		a broken or circular symbolic link.
		"""
		return node and True or False
	exists = lexists

	# Ok, can be improved
	def glob1(self, dirname, pattern):
		"""Return a list of files matching a dirname pattern
		non-recursively.

		Unlike glob.glob1 raises exception if os.listdir() fails.
		"""
		names = self.listdir(dirname)
		if pattern[0] != '.':
			names = filter(lambda x: x.path[0] != '.', names)
		return fnmatch.filter(names, pattern)

	# --- Listing utilities

	# note: the following operations are no more blocking

	# Ok
	def get_list_dir(self, path):
		""""Return an iterator object that yields a directory listing
		in a form suitable for LIST command.
		"""
		if self.isdir(path):
			listing = self.listdir(path)
			#listing.sort()
			return self.format_list(path and path.path or '/', listing)
		# if path is a file or a symlink we return information about it
		elif self.isfile(path):
			basedir, filename = os.path.split(path.path)
			self.lstat(path)  # raise exc in case of problems
			return self.format_list(basedir, [filename])


	# Ok
	def get_stat_dir(self, rawline):
		"""Return an iterator object that yields a list of files
		matching a dirname pattern non-recursively in a form
		suitable for STAT command.

		 - (str) rawline: the raw string passed by client as command
		 argument.
		"""
		ftppath = self.ftpnorm(rawline)
		if not glob.has_magic(ftppath):
			return self.get_list_dir(self.ftp2fs(rawline))
		else:
			basedir, basename = os.path.split(ftppath)
			if glob.has_magic(basedir):
				return iter(['Directory recursion not supported.\r\n'])
			else:
				basedir = self.ftp2fs(basedir)
				listing = self.glob1(basedir, basename)
				if listing:
					listing.sort()
				return self.format_list(basedir, listing)

	# Ok
	def format_list(self, basedir, listing, ignore_err=True):
		"""Return an iterator object that yields the entries of given
		directory emulating the "/bin/ls -lA" UNIX command output.

		 - (str) basedir: the absolute dirname.
		 - (list) listing: the names of the entries in basedir
		 - (bool) ignore_err: when False raise exception if os.lstat()
		 call fails.

		On platforms which do not support the pwd and grp modules (such
		as Windows), ownership is printed as "owner" and "group" as a
		default, and number of hard links is always "1". On UNIX
		systems, the actual owner, group, and number of links are
		printed.

		This is how output appears to client:

		-rw-rw-rw-   1 owner   group	7045120 Sep 02  3:47 music.mp3
		drwxrwxrwx   1 owner   group		  0 Aug 31 18:50 e-books
		-rw-rw-rw-   1 owner   group		380 Sep 02  3:40 module.py
		"""
		for file in listing:
			try:
				st = self.lstat(file)
			except os.error:
				if ignore_err:
					continue
				raise
			perms = filemode(st.st_mode)  # permissions
			nlinks = st.st_nlink  # number of links to inode
			if not nlinks:  # non-posix system, let's use a bogus value
				nlinks = 1
			size = st.st_size  # file size
			uname = "owner"
			gname = "group"
			# stat.st_mtime could fail (-1) if last mtime is too old
			# in which case we return the local time as last mtime
			try:
				mtime = time.strftime("%b %d %H:%M", time.localtime(st.st_mtime))
			except ValueError:
				mtime = time.strftime("%b %d %H:%M")

			# formatting is matched with proftpd ls output
			yield "%s %3s %-8s %-8s %8s %s %s\r\n" %(perms, nlinks, uname, gname,
													 size, mtime, file.path.split('/')[-1])

	def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):
		"""Return an iterator object that yields the entries of a given
		directory or of a single file in a form suitable with MLSD and
		MLST commands.

		Every entry includes a list of "facts" referring the listed
		element.  See RFC-3659, chapter 7, to see what every single
		fact stands for.

		 - (str) basedir: the absolute dirname.
		 - (list) listing: the names of the entries in basedir
		 - (str) perms: the string referencing the user permissions.
		 - (str) facts: the list of "facts" to be returned.
		 - (bool) ignore_err: when False raise exception if os.stat()
		 call fails.

		Note that "facts" returned may change depending on the platform
		and on what user specified by using the OPTS command.

		This is how output could appear to the client issuing
		a MLSD request:

		type=file;size=156;perm=r;modify=20071029155301;unique=801cd2; music.mp3
		type=dir;size=0;perm=el;modify=20071127230206;unique=801e33; ebooks
		type=file;size=211;perm=r;modify=20071103093626;unique=801e32; module.py
		"""
		permdir = ''.join([x for x in perms if x not in 'arw'])
		permfile = ''.join([x for x in perms if x not in 'celmp'])
		if ('w' in perms) or ('a' in perms) or ('f' in perms):
			permdir += 'c'
		if 'd' in perms:
			permdir += 'p'
		type = size = perm = modify = create = unique = mode = uid = gid = ""
		for basename in listing:
			file = os.path.join(basedir, basename)
			try:
				st = self.stat(file)
			except OSError:
				if ignore_err:
					continue
				raise
			# type + perm
			if stat.S_ISDIR(st.st_mode):
				if 'type' in facts:
					if basename == '.':
						type = 'type=cdir;'
					elif basename == '..':
						type = 'type=pdir;'
					else:
						type = 'type=dir;'
				if 'perm' in facts:
					perm = 'perm=%s;' %permdir
			else:
				if 'type' in facts:
					type = 'type=file;'
				if 'perm' in facts:
					perm = 'perm=%s;' %permfile
			if 'size' in facts:
				size = 'size=%s;' %st.st_size  # file size
			# last modification time
			if 'modify' in facts:
				try:
					modify = 'modify=%s;' %time.strftime("%Y%m%d%H%M%S",
										   time.localtime(st.st_mtime))
				except ValueError:
					# stat.st_mtime could fail (-1) if last mtime is too old
					modify = ""
			if 'create' in facts:
				# on Windows we can provide also the creation time
				try:
					create = 'create=%s;' %time.strftime("%Y%m%d%H%M%S",
										   time.localtime(st.st_ctime))
				except ValueError:
					create = ""
			# UNIX only
			if 'unix.mode' in facts:
				mode = 'unix.mode=%s;' %oct(st.st_mode & 0777)
			if 'unix.uid' in facts:
				uid = 'unix.uid=%s;' %st.st_uid
			if 'unix.gid' in facts:
				gid = 'unix.gid=%s;' %st.st_gid
			# We provide unique fact (see RFC-3659, chapter 7.5.2) on
			# posix platforms only; we get it by mixing st_dev and
			# st_ino values which should be enough for granting an
			# uniqueness for the file listed.
			# The same approach is used by pure-ftpd.
			# Implementors who want to provide unique fact on other
			# platforms should use some platform-specific method (e.g.
			# on Windows NTFS filesystems MTF records could be used).
			if 'unique' in facts:
				unique = "unique=%x%x;" %(st.st_dev, st.st_ino)

			yield "%s%s%s%s%s%s%s%s%s %s\r\n" %(type, size, perm, modify, create,
												mode, uid, gid, unique, basename)

