from Tkinter import *
import tkFileDialog
import config as cf

fields = 'Cell Type', 'Cell Subtype'
cell_type = ""
cell_subtype = ""

result_file = "result.txt"
image_name = cf.image_path
has_quit = False

def select_image():
    # Currently does not work
    return tkFileDialog.askopenfilename(initialdir="../samples/",title="Select File",filetypes=(("png files","*.png"),("jpeg files","*.jpg")))

def fetch(entries):
    for entry in entries:
        field = entry[0]
        text = entry[1].get()
        print('%s: "%s"' %(field, text))

def makeform(root, fields):
    entries = []
    for field in fields:
        row = Frame(root)
        lab = Label(row, width=15, text=field, anchor='w')
        ent = Entry(row)

        row.pack(side=TOP, fill=X, padx=5, pady=5)
        lab.pack(side=LEFT)

        ent.pack(side=RIGHT, expand=YES, fill=X)
        entries.append((field, ent))

    return entries

def save_and_quit(image_name, ents, root, RefPt):
    global cell_type, cell_subtype
    global has_quit

    with open(result_file, 'ab') as f:
        f.write(image_name+","+str(RefPt[0])+","+str(RefPt[1]))
        for ent in ents:
            (field, ans) = ent
            f.write(","+ans.get())

        f.write("\n")

    has_quit = False
    root.destroy()

def quit_button_callback(root):
    global has_quit

    has_quit = True
    root.destroy()

def enter_label(image_name, RefPt):
    root = Tk()
    root.title("Cell Labler")
    ents = makeform(root, fields)
    root.bind('<Return>', (lambda event, im=image_name, e=ents, r=root, ref=RefPt: save_and_quit(im, e, r, ref)))

    b2 = Button(root, text='Quit', command=(lambda: quit_button_callback(root)))
    b2.pack(side=RIGHT, padx=5, pady=5)

    b1 = Button(root, text='Confirm', command=(lambda: save_and_quit(image_name, ents, root, RefPt)))
    b1.pack(side=RIGHT, padx=5, pady=5)

    root.mainloop()

    return has_quit

if __name__ == "__main__":
    # Testout code
    root = Tk()
    ents = makeform(root, fields)
    RefPt = [(0,0), (0,0)]
    root.bind('<Return>', (lambda event, im=image_name, e=ents, r=root, ref=RefPt: save_and_quit(im, e, r, ref)))

    b2 = Button(root, text='Quit', command=(lambda: quit_button_callback(root)))
    b2.pack(side=RIGHT, padx=5, pady=5)

    b1 = Button(root, text='Confirm', command=(lambda: save_and_quit(image_name, ents, root, RefPt)))
    b1.pack(side=RIGHT, padx=5, pady=5)

    root.mainloop()
