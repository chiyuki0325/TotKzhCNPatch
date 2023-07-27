import tkinter as tk
from tkinter import ttk
import os
from functools import partial



class CallbackText(tk.Text):
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        # avoid error when copying
        if command == 'get' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'): return

        # avoid error when deleting
        if command == 'delete' and (args[0] == 'sel.first' and args[1] == 'sel.last') and not self.tag_ranges('sel'): return

        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ('insert', 'delete', 'replace'):
                    self.event_generate('<<TextModified>>')

        return result

class ConfirmationPrompt(): # Save prompt on close, etc.
    def __init__(self, parent, title, confirm_message, options, initial_choice):
        self.confirmationbox = tk.Toplevel(parent)
        self.confirmationbox.title(title)
        self.confirmationbox.resizable(width = False, height= False)
        self.confirmationbox['padx'] = 5
        self.confirmationbox['pady'] = 5

        self.confirmationbox.wm_transient(parent)

        self.choice = initial_choice

        self.info_label = ttk.Label(self.confirmationbox, text=confirm_message)
        self.info_label.grid(row=0, column=0, columnspan=5)

        Buttons_List = []
        self.entry_list = []
        for i in range(len(options)):
            Buttons_List += [ttk.Button(self.confirmationbox, text=options[i], command= partial(self.on_choice, choice=i ) ).grid(row=1+(i//5 % 100), column=i % 5)]
            self.entry_list += [i]

        self.confirmationbox.mainloop()
    
    def on_choice(self, choice):
        self.choice = self.entry_list[choice]
        self.confirmationbox.quit()
        self.confirmationbox.destroy()

def get_initial_directory(cache_dir):
    if os.path.isfile(cache_dir):
        initial_dir = open(cache_dir, 'r').read()
        if not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()
        return initial_dir
    else:
        return os.getcwd()


def closest_index(string, sub, start): # Find the closest index of a substring to a given index (before or after).
    
    sub_len = len(sub)
    ind = start

    if sub in string:

        if sub not in string[start:]: # Only check before given index.
            while True:
                if string[ind:ind+sub_len] == sub:
                    break
                ind -= 1

        elif sub not in string[:start]: # Only check after given index.
            while True:
                if string[ind:ind+sub_len] == sub:
                    break
                ind += 1
        
        else:
            dif = 0
            while True: # Check before and after.
                ind = start + dif
                if string[ind:ind+sub_len] == sub:
                    break
                ind = start - dif
                if string[ind:ind+sub_len] == sub:
                    break
                dif += 1

    else:
        ind = None

    return ind

def closest_punctuation(string, ind): # Find the closest punctuation after a given index (ignoring certain abbreviations).
    IgnoreList = ["0.", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "br0z.", "bros.", "co.", "dr.", "e.", "mrs.", "ms.", "prof.", "mr.", "sr.", "jr.", "vs.", "v.s."]

    while ind > 0:

        if ". " not in string[:ind] and "... " not in string[:ind] and "… " not in string[:ind] and "! " not in string[:ind] and "? " not in string[:ind]: # If no punctuation present in remainder of string, return None.
            return None

        while string[ind:ind+2] not in [". ","... ","… ","! ","? "]: # Continue until punctuation is found.
            ind -= 1

        if " " not in string[:ind]: # If no spaces present in remainder of string, return None.
            return None

        sp_ind = string.rindex(" ", 0, ind)+1
        if string[sp_ind:ind+1].lower() not in IgnoreList: # If the punctuation found is not part of an abbreviation, return the index.
            return ind+1
        else:
            ind -= 1

    return None # A complete iteration through the string without finding anything; return None.



def code_count(string, sub):
    string_len = len(string)
    count = rind = ind = 0
    while ind < string_len:
        if string[ind] == "\\":
            ind += 1
        elif string[ind] == "<":
            rind = ind
            ind = string.index(">", ind)
            if string[rind:ind+1] == sub:
                count += 1
        ind += 1
    return count



def code_split(string, sub):
    List = []
    string_len = len(string)
    rind = ind = 0
    while ind < string_len:
        if string[ind] == "\\":
            ind += 1
        elif string[ind] == "<":
            mind = ind
            ind = string.index(">", ind)+1
            if string[mind:ind] == sub:
                List += (string[rind:mind],)
                rind = ind
        ind += 1
    if rind < string_len:
        List += (string[rind:],)
    return List