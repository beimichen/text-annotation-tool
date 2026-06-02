#!/usr/bin/env python3

import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, IntVar

APPLYING_LABELS = True
REMOVING_LABELS = False

DEFAULT_CONTEXT_SIZE = 10

def padstr(str, strwidth, fillchar=' '):
	return str + fillchar*(strwidth-len(str))

def deprotect(s):
	return s.replace('[RET]','\n').replace('[TAB]','\t')

def hash_me(s, mod=2**40):
	value = 0
	for i in range(len(s)):
		value = (value + ord(s[i])**(i+1)) % mod
	return value

class ContextualizedString:
	def __init__(self, args):
		self.prev = args[0].split('\n')[-1]
		self.this = args[1]
		self.next = args[2].split('\n')[0]

	def __gt__(self, other):
		return self.get_full_context() > other.get_full_context()
	
	def __lt__(self, other):
		return self.get_full_context() < other.get_full_context()
	
	def __eq__(self, other):
		return self.get_full_context() == other.get_full_context()

	def __hash__(self):
		return hash_me(self.get_full_context())

	def get_full_context(self):
		return self.prev + self.this + self.next
	
	def get_delimited_context(self, delimiter='\t'):
		return self.prev + delimiter + self.this + delimiter + self.next

	def get_prev(self):
		return self.prev
	
	def get_focus(self):
		return self.this
	
	def get_next(self):
		return self.next

class BindingColors:
	def __init__(self, fg, bg):
		self.fg = fg
		self.bg = bg

class ContextManagerDialog(tk.Toplevel):

	def __init__(self, editor, **kwargs):
		super().__init__(editor, **kwargs)
		self.editor = editor

		topmost = tk.Frame(self)
		topmost.pack(fill='x')

		tk.Button(topmost, text='Save', command=self.save).pack(side='left')
		tk.Button(topmost, text='Load', command=self.load).pack(side='left')

		topframe = tk.Frame(self)
		topframe.pack(expand=True, anchor='center')

		label = tk.Label(topframe, text="Hash:")
		label.pack()
		self.hash_box = tk.Entry(topframe)
		self.hash_box.pack()

		self.existing_contexts = tk.Text(self, height=20)
		self.existing_contexts.pack()

		self.refresh()

		buttonframe = tk.Frame(self)
		buttonframe.pack(side='bottom', fill='x')

		closebutton = tk.Button(buttonframe, text="Close",command=self.dismiss)
		closebutton.pack(side='right')
		removebutton = tk.Button(buttonframe, text="Remove Hash", command=self.remove_hash)
		removebutton.pack(side='left')

		self.hash_box.focus()
		self.title("Context Manager")
		self.protocol('WM_DELETE_WINDOW', self.dismiss)
	
	def dismiss(self):
		self.editor.context_manager = None
		self.withdraw()

	def save(self, event=None):
		filename = filedialog.asksaveasfilename()
		if filename:
			try:
				contexts = []
				for label in self.editor.textwidget.boundLabels:
					for context in self.editor.textwidget.boundLabels[label]:
						contexts.append(label + '\t' + context.get_delimited_context())
				open(filename,'w').write('\n'.join(contexts))
			except:
				# an error occurred
				pass

	def load(self, event=None):
		filename = filedialog.askopenfilename()
		if filename:
			try:
				contents = open(filename,'r').read()
				for line in contents.split('\n'):
					args = line.split('\t')
					self.editor.textwidget._register_context(args[0],ContextualizedString(args[1:]))
				self.editor.textwidget._apply_all_labels()
			except:
				# something went wrong
				pass
		self.refresh()

	def refresh(self):
		self.existing_contexts.delete('1.0','end')

		text = self.editor.textwidget
		for label in text.boundLabels:
			self.existing_contexts.insert('end', label + '\n')
			for context in text.boundLabels[label]:
				hashable = label + '\t' + context.get_delimited_context()
				self.existing_contexts.insert('end', str(hash_me(hashable)) + '\t' + hashable + '\n')
		self.hash_box.delete(0,'end')

	def remove_hash(self, event=None):
		text = self.editor.textwidget
		if  len(self.hash_box.get()):
			for label in text.boundLabels:
				to_remove = []
				for context in text.boundLabels[label]:
					hashable = label + '\t' + context.get_delimited_context()
					if str(hash_me(hashable)) == self.hash_box.get():
						to_remove.append((label, context))

				for lab, cont in to_remove:
					self.editor.textwidget._unregister_context(lab, cont)

					# do some jiggering to do the removal without changing settings
					saved_state = self.editor.get_application_status()
					self.editor.set_application_status(REMOVING_LABELS)
					self.editor.textwidget._apply_label(cont, lab)
					self.editor.set_application_status(saved_state)
		else:
			# show a messagebox saying all the fields need to be filled
			pass

		self.editor.refresh_managers()

class LabelManagerDialog(tk.Toplevel):

	def __init__(self, editor, **kwargs):
		super().__init__(editor, **kwargs)
		self.editor = editor

		topmost = tk.Frame(self)
		topmost.pack(fill='x')

		tk.Button(topmost, text='Save', command=self.save).pack(side='left')
		tk.Button(topmost, text='Load', command=self.load).pack(side='left')

		topframe = tk.Frame(self)
		topframe.pack(expand=True, anchor='center')

		label = tk.Label(topframe, text="Label:")
		label.pack()
		self.label_box = tk.Entry(topframe)
		self.label_box.pack()
		self.label_box.bind('<Return>', self.create_label)

		self.existing_labels = tk.Text(self, height=20)
		self.existing_labels.pack()

		self.refresh()

		buttonframe = tk.Frame(self)
		buttonframe.pack(side='bottom', fill='x')

		closebutton = tk.Button(buttonframe, text="Close",command=self.dismiss)
		closebutton.pack(side='right')
		createbutton = tk.Button(buttonframe, text="Create Label", command=self.create_label)
		createbutton.pack(side='left')
		removebutton = tk.Button(buttonframe, text="Remove Label", command=self.remove_label)
		removebutton.pack(side='left')

		self.label_box.focus()
		self.title("Label Manager")
		self.protocol('WM_DELETE_WINDOW', self.dismiss)
	
	def dismiss(self):
		self.editor.label_manager = None
		self.withdraw()

	def save(self, event=None):
		filename = filedialog.asksaveasfilename()
		if filename:
			try:
				open(filename,'w').write('\n'.join(sorted([x for x in self.editor.textwidget.labels])))
			except:
				# an error occurred
				pass

	def load(self, event=None):
		filename = filedialog.askopenfilename()
		if filename:
			try:
				contents = open(filename,'r').read()
				for label in contents.split('\n'):
					self.label_box.delete(0,'end')
					self.label_box.insert(0,label)
					self.create_label(label)
			except:
				# something went wrong
				pass

	def refresh(self):
		self.existing_labels.delete('1.0','end')
		self.existing_labels.insert('end','\n'.join(sorted([x for x in self.editor.textwidget.labels])))
		self.label_box.delete(0,'end')

	def create_label(self, event=None):
		text = self.editor.textwidget
		if  len(self.label_box.get()):
			text._register_label(self.label_box.get())
		else:
			# show a messagebox saying all the fields need to be filled
			pass
		self.refresh()

	def remove_label(self, event=None):
		text = self.editor.textwidget
		if  len(self.label_box.get()):
			text._unregister_label(self.label_box.get())
		else:
			# show a messagebox saying all the fields need to be filled
			pass

		self.editor.refresh_managers()

class KeyBindingManagerDialog(tk.Toplevel):

	def __init__(self, editor, **kwargs):
		super().__init__(editor, **kwargs)
		self.editor = editor

		topmost = tk.Frame(self)
		topmost.pack(fill='x')

		tk.Button(topmost, text='Save', command=self.save).pack(side='left')
		tk.Button(topmost, text='Load', command=self.load).pack(side='left')

		topframe = tk.Frame(self)
		topframe.pack(expand=True, anchor='center')

		label = tk.Label(topframe, text="Key Binding:")
		label.pack()
		self.key_binding = tk.Entry(topframe)
		self.key_binding.pack()

		label = tk.Label(topframe, text="Label to Bind:")
		label.pack()
		self.label_category = tk.Entry(topframe)
		self.label_category.pack()

		label = tk.Label(topframe, text="Foreground Color:")
		label.pack()
		self.fg_color = tk.Entry(topframe)
		self.fg_color.pack()

		label = tk.Label(topframe, text="Background Color:")
		label.pack()
		self.bg_color = tk.Entry(topframe)
		self.bg_color.pack()

		self.bg_color.bind('<Return>', self.create_binding)

		self.existing_labels = tk.Text(self, height=20)
		self.existing_labels.pack()

		self.refresh()

		buttonframe = tk.Frame(self)
		buttonframe.pack(side='bottom', fill='x')

		closebutton = tk.Button(buttonframe, text="Close",command=self.dismiss)
		closebutton.pack(side='right')
		findbutton = tk.Button(buttonframe, text="Create Tag", command=self.create_binding)
		findbutton.pack(side='left')
		removebutton = tk.Button(buttonframe, text="Remove Tag", command=self.remove_binding)
		removebutton.pack(side='left')
		editbutton = tk.Button(buttonframe, text="Edit Tag", command=self.edit_binding)
		editbutton.pack(side='left')

		self.key_binding.focus()
		self.title("KeyBinding Manager")
		self.protocol('WM_DELETE_WINDOW', self.dismiss)
	
	def dismiss(self):
		self.editor.binding_manager = None
		self.withdraw()

	def _bindings_to_string(self, func):
		text = self.editor.textwidget
		sortable = []
		for binding, label in text.bindings.items():
			printable = [binding] + [label] + [text.bindingColors[binding].fg] + [text.bindingColors[binding].bg]
			sortable.append(''.join([func(x) for x in printable]) + '\n')
		return ''.join(sorted(sortable))

	def save(self, event=None):
		filename = filedialog.asksaveasfilename()
		if filename:
			try:
				open(filename,'w').write(self._bindings_to_string(lambda x: x+'\t'))
			except:
				# an error occurred
				pass

	def load(self, event=None):
		filename = filedialog.askopenfilename()
		if filename:
			try:
				contents = open(filename,'r').read()
				for record in contents.split('\n'):
					param = [x for x in record.split('\t') if len(x)]
					self.key_binding.delete(0,'end')
					self.key_binding.insert(0,param[0])
					self.label_category.delete(0,'end')
					self.label_category.insert(0,param[1])
					self.fg_color.delete(0,'end')
					self.fg_color.insert(0,param[2])
					self.bg_color.delete(0,'end')
					self.bg_color.insert(0,param[3])
					self.create_binding()

			except:
				# something went wrong
				pass

	def refresh(self):
		self.existing_labels.delete('1.0','end')
		self.existing_labels.insert('end',self._bindings_to_string(lambda x: padstr(x,20)))

		self.key_binding.delete(0,'end')
		self.label_category.delete(0,'end')
		self.fg_color.delete(0,'end')
		self.bg_color.delete(0,'end')

		self.key_binding.focus()

	def create_binding(self, event=None):
		text = self.editor.textwidget
		if  len(self.key_binding.get()) and len(self.label_category.get()) and len(self.fg_color.get()) and len(self.bg_color.get()):
			text._register_binding(self.key_binding.get(), self.label_category.get(), self.fg_color.get(), self.bg_color.get())
		else:
			# show a messagebox saying all the fields need to be filled
			pass
		self.refresh()

	def remove_binding(self, event=None):
		text = self.editor.textwidget
		if  len(self.key_binding.get()):
			text._unregister_binding(self.key_binding.get(), self.label_category.get())
		else:
			# show a messagebox saying all the fields need to be filled
			pass

		self.editor.refresh_managers()

	def edit_binding(self, event=None):
		text = self.editor.textwidget
		if  len(self.key_binding.get()) and len(self.label_category.get()) and len(self.fg_color.get()) and len(self.bg_color.get()):
			if text._unregister_binding(self.key_binding.get(), self.label_category.get()):
				text._register_binding(self.key_binding.get(), self.label_category.get(), self.fg_color.get(), self.bg_color.get())
		else:
			# show a messagebox saying all the fields need to be filled
			pass
		self.refresh()

class EditorText(tk.Text):

	def __init__(self, textarea, parent, **kwargs):
		super().__init__(textarea, **kwargs)
		self.parent = parent

		self.tag_config('sel', background='black', foreground='yellow')

		self.labels = set()
		self.bindings = dict() # of (key, label)
		self.bindingColors = dict() # (key, BindingColors)
		self.boundLabels = dict() # of (label, set(context, searchstring))

		self.context_size = DEFAULT_CONTEXT_SIZE

		self.bind('<Key>', self._on_key)
		self.bind('<Control-w>', self.toggle_context)

	def get_context_size(self):
		return self.context_size
	
	def editor_state(self):
		return self.parent.get_application_status()
	
	def toggle_context(self, event):
		if self.context_size:
			self.context_size = 0
		else:
			self.context_size = DEFAULT_CONTEXT_SIZE
		self.parent._update_statusbar_label()
		return 'break'

	def _on_key(self, event):
		if event.keysym in self.bindings:
			prev, this, next = '', '', ''
			try:
				prev = self.get('sel.first - %i chars' % self.context_size, 'sel.first')
				this = self.get('sel.first','sel.last')
				next = self.get('sel.last','sel.last + %i chars' % self.context_size)
			except:
				# nothing was selected
				pass

			if len(this):
				label = self.bindings[event.keysym]

				contextualizedString = ContextualizedString([prev, this, next])

				if self.editor_state() == APPLYING_LABELS:
					self._register_context(label, contextualizedString)
				else:
					self._unregister_context(label, contextualizedString)

				self._apply_label(contextualizedString, label)

				self.parent.refresh_managers()

		return 'break'
	
	def _register_context(self, label, contextualizedString):
		if label in self.boundLabels:
			self.boundLabels[label].add(contextualizedString)

			# remove other labels to prevent putting multiple labels on a context
			for local_label in self.boundLabels:
				if local_label != label:
					self._unregister_context(local_label, contextualizedString)

	def _unregister_context(self, label, contextualizedString):
		if label in self.boundLabels:
			if contextualizedString in self.boundLabels[label]:
				self.boundLabels[label].remove(contextualizedString)

	def _register_label(self, label):
		self.labels.add(label)
		self.boundLabels[label] = set()

	def _unregister_label(self, label):
		if label in self.labels:
			assert label in self.boundLabels

			disposable_bindings = [key for key, value in self.bindings.items() if value == label]
			for binding in disposable_bindings:
				self.bindings.pop(binding)

			self.labels.remove(label)
			self.boundLabels.pop(label)
			self.tag_delete(label)

	def _register_binding(self, key_binding, label, fg_color, bg_color):
		try:
			if label in self.labels and key_binding not in self.bindings:
				self.tag_config(label, foreground=fg_color, background=bg_color)
				self.bindings[key_binding] = label
				self.bindingColors[key_binding] = BindingColors(fg_color, bg_color)
		except:
			# show a message saying the color is messed up
			pass

	def _unregister_binding(self, key_binding, label):
		if key_binding in self.bindings and self.bindings[key_binding] == label:
			self.bindings.pop(key_binding)
			self.bindingColors.pop(key_binding)
			return True
		else:
			return False

	def _apply_all_labels(self):
		self.parent.set_application_status(APPLYING_LABELS)

		for label in self.boundLabels:
			for context in self.boundLabels[label]:
				self._apply_label(context, label)

	def _apply_label(self, contextualizedString, label, test=False):
		searchable = self.get('1.0','end').split('\n')

		priorlen = len(contextualizedString.get_prev())
		sequence = contextualizedString.get_full_context()
		taggable = contextualizedString.get_focus()
		for line in range(len(searchable)):
			pos = 0
			while pos != -1:
				pos = searchable[line].find(sequence, pos)
				if pos != -1:
					if test:
						return True

					if self.editor_state() == APPLYING_LABELS:
						self.tag_add(label, str(line+1)+'.'+str(pos+priorlen), str(line+1)+'.'+str(pos+priorlen+len(taggable)))
					else:
						self.tag_remove(label, str(line+1)+'.'+str(pos+priorlen), str(line+1)+'.'+str(pos+priorlen+len(taggable)))
					pos += len(sequence)
		return False

class Editor(tk.Tk):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.label_manager = None
		self.binding_manager = None
		self.context_manager = None

		self._open_file = None
		self._save_file = None
		self._seen_hashes = set()

		self.doc_hash = ''
		self.doc_text = ''

		self.application_status = IntVar()

		self.topbar = tk.Frame(self)
		self.topbar.pack(fill='x')

		textarea = tk.Frame(self)
		textarea.pack(fill='both', expand=True)
		self.textwidget = EditorText(textarea, self, height=20, width=60, font=("Helvetica", 18), wrap=tk.WORD)
		self.textwidget.pack(side='left', fill='both', expand=True)
		scrollbar = tk.Scrollbar(textarea)
		scrollbar.pack(side='left', fill='y')
		self.textwidget['yscrollcommand'] = scrollbar.set
		scrollbar['command'] = self.textwidget.yview

		self.statusbar_text = tk.StringVar()
		self.statusbar = tk.Label(self, anchor='w', relief='sunken', textvariable=self.statusbar_text)
		self.statusbar.pack(fill='x')

		menucontent = [
			("File", [
				("Open Collection", "Ctrl+O", '<Control-o>', self.open_file),
				("Load Next", "Ctrl+N", '<Control-n>', self.load_next_document),
				("Save and Load Next", "Ctrl+S", '<Control-s>', self.save_and_load_next),
			]),
			("Edit", [
				("Manage Labels", "Ctrl+L", '<Control-l>', self.manage_labels),
				("Manage Bindings", "Ctrl+T", '<Control-t>', self.manage_bindings),
				("Manage Contexts", "Ctrl+D", '<Control-d>', self.manage_contexts),
			]),
		]
		menubar = self['menu'] = tk.Menu(self)
		for title, menuitems in menucontent:
			menu = tk.Menu(menubar, tearoff=False)
			for item in menuitems:
				if item is None:
					menu.add_separator()
					continue
				text, accelerator, binding, command = item
				menu.add_command(label=text, accelerator=accelerator,
								 command=command)
				self._bind_menu_command(binding, command)
			menubar.add_cascade(label=title, menu=menu)

		if self.topbar is not None:
			# menucontent[0][1] is content of the File menu
			for item in menucontent[0][1]:
				if item is None:
					# it's a separator, we'll add an empty frame that
					# fills extra space
					tk.Frame(self.topbar).pack(side='left', expand=True)
					continue
				text, accelerator, binding, command = item
				button = tk.Button(self.topbar, text=text, command=command)
				button.pack(side='left')
		
		tk.Radiobutton(self.topbar, text='Remove', variable=self.application_status, value=REMOVING_LABELS, command=self._update_statusbar_label).pack(side='right')
		tk.Radiobutton(self.topbar, text='Apply', variable=self.application_status, value=APPLYING_LABELS, command=self._update_statusbar_label).pack(side='right')
		self.application_status.set(APPLYING_LABELS)
		self._update_statusbar_label()

		self.title("JX Annotator Tool")
		self.protocol('WM_DELETE_WINDOW', self.quit)
		self.textwidget.focus()

	def _bind_menu_command(self, binding, command):
		def bindcallback(event):
			command()
			return 'break'

		self.bind(binding, bindcallback)
		self.textwidget.bind(binding, bindcallback)

	def _update_statusbar_label(self):
		text = 'Context Size: %i'%self.textwidget.get_context_size()
		if self.application_status.get() == APPLYING_LABELS:
			text += '  Editor State: Applying Labels'
		else:
			text += '  Editor State: Removing Labels'
		self.statusbar_text.set(text)

	def set_application_status(self, value):
		self.application_status.set(value)

	def get_application_status(self):
		return self.application_status.get()

	def save_and_load_next(self):
		if self._save_file:
			try:
				content = 'dochash=' + self.doc_hash + '\n'

				for label in self.textwidget.boundLabels:
					for context in self.textwidget.boundLabels[label]:
						if self.textwidget._apply_label(context, label, True):
							content += 'context=' + label + '\t' + context.get_prev() + '\t' + context.get_focus() + '\t' + context.get_next() + '\n'

				content += 'doctext=' + self.doc_text + '\n'

				self._save_file.write(content)
				self._save_file.flush()

				self._seen_hashes.add(self.doc_hash)

				self.load_next_document()
			except:
				# not able to save file
				pass
		else:
			# no save file specified
			pass

	def load_next_document(self):
		if self._open_file:
			try:
				self.doc_hash = ''
				while self.doc_hash == '' or self.doc_hash in self._seen_hashes:
					content = self._open_file.readline()

					assert len(content.split('\t')) == 2

					self.doc_hash = content.split('\t')[0]
					self.doc_text = content.split('\t')[1]

				self.textwidget.delete('0.0', 'end')
				self.textwidget.insert('0.0', deprotect(self.doc_text))

				self.textwidget._apply_all_labels()

			except:
				pass
		else:
			self.open_file()

	def open_file(self):
		filename = filedialog.askopenfilename()
		if filename and os.path.exists(filename):
			try:
				self._open_file = open(filename,'r',encoding='utf-8')
				self._save_file = open(filename+'_annotations_'+str(int(time.time())),'w')

				basepath = os.path.dirname(filename)
				filename = os.path.basename(filename)

				self._seen_hashes = set()
				for f in os.listdir(basepath):
					if f.find(filename+'_annotations_') != -1:
						print ('loading hashes from',f)
						path = os.path.join(basepath,f)
						with open(path,'r') as annotation_file:
							for line in annotation_file:
								if line.find('dochash=') != -1:
									self._seen_hashes.add(line.replace('dochash=','').replace('\n',''))

				self.load_next_document()

			except:
				# raise a message with some text from the error
				pass

	def refresh_managers(self):
		if self.binding_manager:
			try:
				self.binding_manager.refresh()
			except:
				# couldn't access/refresh key binding manager
				pass

		if self.label_manager:
			try:
				self.label_manager.refresh()
			except:
				# couldn't access/refresh label manager
				pass

		if self.context_manager:
			try:
				self.context_manager.refresh()
			except:
				# couldn't access/refresh context manager
				pass

	def manage_bindings(self):
		if self.binding_manager == None:
			self.binding_manager = KeyBindingManagerDialog(self)
		else:
			self.binding_manager.focus()
		return 'break'

	def manage_labels(self):
		if self.label_manager == None:
			self.label_manager = LabelManagerDialog(self)
		else:
			self.label_manager.focus()
		return 'break'

	def manage_contexts(self):
		if self.context_manager == None:
			self.context_manager = ContextManagerDialog(self)
		else:
			self.context_manager.focus()
		return 'break'

def main():

	editor = Editor()
	editor.title("Text Annotation Tool")
	editor.mainloop()

if __name__ == '__main__':
	main()
