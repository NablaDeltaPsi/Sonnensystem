
global GUI_version; GUI_version = '3.1'

import tkinter as tk
import tkinter.font
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkcairo as tkcairo
import datetime as dt
import os
import time
import warnings
import ctypes
import astropy as ap
import astropy.coordinates as apc
mpl.use('TkCairo')

def blanks(number):
    string = ""
    for i in range(number):
        string = string + " "
    return string

def pol2cart(rho, phi):
    x = np.multiply(rho, np.cos(phi / 180 * np.pi))
    y = np.multiply(rho, np.sin(phi / 180 * np.pi))
    return(x, y)

def pts(*args):
    # accepts str, str+'p', int, float and returns sum as str+'p'
    # '-' sets the following argument negative
    # pts(0.5, '1.5', '-', '3p') = '-1p'
    number = 0
    factor = 1
    for i in range(len(args)):
        if args[i]=='-':
            factor = -1
        elif args[i] == '':
            factor = 1
            continue
        else:
            try:
                number = number + factor*float(args[i])
            except:
                if args[i][len(args[i])-1] == 'p':
                    try:
                        number = number + factor*float(args[i][0:len(args[i])-1])
                    except:
                        warnings.warn("Could not add value to points!", stacklevel=2)
                else:
                    warnings.warn("Could not add value to points!", stacklevel=2)
            factor = 1
    return str(number) + "p"

def select_larger_zero(array, check):
    if not (len(array)==len(check)):
        return array
    new = np.array([])
    aufstkn_index = 0
    for i in range(len(check)):
        if (check[i] > 0) and (check[i-1] < 0):
            aufstkn_index = i
    for i in range(aufstkn_index, len(check)):
        if check[i] > 0:
            new = np.append(new, array[i])
    for i in range(aufstkn_index):
        if check[i] > 0:
            new = np.append(new, array[i])
    return new



# ----------------------------------------------
# CLASS NEWGUI
# ----------------------------------------------
class NewGUI():

    # guisize and fontsize in points, xpos and ypos in pixels!!
    def __init__(self, guisize, fontsize, xpos, ypos, d, m, y):

        print("NEW GUI SIZE " + str(guisize) + " FONTSIZE " + str(fontsize))

        self.guisize = guisize
        self.fontsize = fontsize
        self.root = tk.Tk()
        self.root.title("Sonnensystem (v" + GUI_version + ")")
        self.root.resizable(False, False)
        self.root.configure(background='black')
        self.output = True
        self.repeat_time = 20
        self.repeat_on = True
        self.repeat_count = 0
        self.view_mode = 0
        self.fix_earth = 0

        # get fontsize
        default_font = tk.font.nametofont("TkDefaultFont")
        text_font = tk.font.nametofont("TkTextFont")
        default_font.configure(size=self.fontsize)
        text_font.configure(size=self.fontsize)

        # guiwidth and guisize
        guiwidth  = int(self.root.winfo_fpixels(pts(self.guisize)))
        guiheight = int(self.root.winfo_fpixels(pts(self.guisize + 4.5*self.fontsize)))

        self.root.geometry(str(guiwidth) + "x" + str(guiheight) + "+" + str(xpos) + "+" + str(ypos))
        self.root.protocol("WM_DELETE_WINDOW",  self.on_close)

        try:
            self.root.iconbitmap('Sonnensystem_icon.ico')
        except:
            print("Icon nicht gefunden... Fahre fort.")

        # bind actions
        self.root.unbind_all("<Tab>")
        self.root.unbind_all("<<NextWindow>>")
        self.root.unbind_all("<<PrevWindow>>")
        self.root.bind('<Return>', self.replot)
        self.root.bind('<Right>', self.replot_p)
        self.root.bind('<Left>',  self.replot_m)
        self.root.bind('<Control-Right>', self.replot_strg_p)
        self.root.bind('<Control-Left>', self.replot_strg_m)
        self.root.bind('<Up>',    self.switch_elongation_selection_rev)
        self.root.bind('<Down>',  self.switch_elongation_selection)
        self.root.bind('<Tab>', self.switch_view)
        self.root.bind('<Shift-Tab>', self.switch_view_rev)
        self.root.bind('<h>',  self.replot_today)
        self.root.bind('<j>',  self.replot_2000)
        self.root.bind("<MouseWheel>", self.replot_mouse_wheel)
        self.root.bind('<e>',  self.replot_elongation_p)
        self.root.bind('<Control-e>',  self.replot_elongation_m)
        self.root.bind('<f>',  self.switch_fix_earth)
        #self.root.bind("<KeyPress-Right>", self.replot_step)
        #self.root.bind("<KeyRelease-Right>", self.replot_stop)

        # PLANETEN
        # https://de.wikipedia.org/wiki/Liste_der_Planeten_des_Sonnensystems
        self.all_planets = []
        #                                                           Periode   Pol          a     Exzen    Perihel     aufstKn
        self.all_planets.append(Planet(self, 'mercury', 'Merkur',  87.96926,  315,   0.38710,  0.20563,  77.45645,   48.33167 ))
        self.all_planets.append(Planet(self, 'venus',   'Venus',   224.7008,  342,   0.72333,  0.00677, 131.53298,   76.68063 ))
        self.all_planets.append(Planet(self, 'earth',   'Erde',    365.2564,   90,   1.00000,  0.01671, 102.94719,  -11.26064 ))
        self.all_planets.append(Planet(self, 'mars',    'Mars',    686.9796,  335,   1.52366,  0.09341, 336.04084,   49.57854 ))
        self.all_planets.append(Planet(self, 'jupiter', 'Jupiter', 4332.820,  183,   5.20336,  0.04837,  14.75385,  100.55615 ))
        self.all_planets.append(Planet(self, 'saturn',  'Saturn',  10755.70,   78,   9.53707,  0.05415,  92.43194,  113.71504 ))
        self.all_planets.append(Planet(self, 'uranus',  'Uranus',  30687.15,   78,  19.19126,  0.04716, 170.96424,   74.22988 ))
        self.all_planets.append(Planet(self, 'neptune', 'Neptun',  60190.03,  327,  30.06896,  0.00858,  44.97135,  131.72169 ))
        self.all_planets.append(Planet(self, 'moon', 'Erdmond', 0, 0, 0.00257, 0, 0, 0 ))

        mydate = dt.date.today()
        width_dm = 1.5*self.fontsize
        width_yr = 3.0*self.fontsize
        width_pl = 7.0*self.fontsize
        width_pm = 0.8*self.fontsize
        width_vw = 2*self.fontsize
        width_sl = 3*self.fontsize
        
        x1 = pts(0*width_dm, 0*width_pm)
        x2 = pts(1*width_dm, 0*width_pm)
        x3 = pts(1*width_dm, 1*width_pm)
        x4 = pts(2*width_dm, 1*width_pm)
        x5 = pts(2*width_dm, 2*width_pm)
        x6 = pts(2*width_dm, 2*width_pm, 1*width_yr)
        x7 = pts(2*width_dm, 3*width_pm, 1*width_yr)

        h1 = pts(1.5*self.fontsize)
        h2 = pts(1.5*self.fontsize/2)

        self.button_view = tk.Button(self.root, text="O", command=self.switch_view)
        self.button_view.place(relx=1, x=pts('-', 4*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_elong = tk.Button(self.root, text="E", command=self.replot_elongation_p)
        self.button_elong.place(relx=1, x=pts('-', 5*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_today = tk.Button(self.root, text="H", command=self.replot_today)
        self.button_today.place(relx=1, x=pts('-', 6*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_today = tk.Button(self.root, text="F", command=self.switch_fix_earth)
        self.button_today.place(relx=1, x=pts('-', 7*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.entry_1 = tk.Entry(self.root, justify='center')
        self.entry_1.place(x=x1, y=0, height=h1, width=pts(width_dm), anchor='nw')
        self.entry_1.insert("0",str(mydate.day))
        self.entry_1.bind('<Right>', self.replot_day_p)
        self.entry_1.bind('<Left>', self.replot_day_m)
        self.entry_1.bind('<Control-Right>', self.replot_3days_p)
        self.entry_1.bind('<Control-Left>', self.replot_3days_m)
        self.entry_1.bind("<MouseWheel>", self.replot_mouse_wheel)

        self.entry_2 = tk.Entry(self.root, justify='center')
        self.entry_2.place(x=x3, y=0, height=h1, width=pts(width_dm), anchor='nw')
        self.entry_2.insert("0",str(mydate.month))
        self.entry_2.bind('<Right>', self.replot_month_p)
        self.entry_2.bind('<Left>', self.replot_month_m)
        self.entry_2.bind("<MouseWheel>", self.replot_mouse_wheel)

        self.entry_3 = tk.Entry(self.root, justify='center')
        self.entry_3.place(x=x5, y=0, height=h1, width=pts(width_yr), anchor='nw')
        self.entry_3.insert("0",str(mydate.year))
        self.entry_3.bind('<Right>', self.replot_year_p)
        self.entry_3.bind('<Left>', self.replot_year_m)
        self.entry_3.bind('<Control-Right>', self.replot_century_p)
        self.entry_3.bind('<Control-Left>', self.replot_century_m)
        self.entry_3.bind('<Control-Up>', self.replot_century_p)
        self.entry_3.bind('<Control-Down>', self.replot_century_m)
        self.entry_3.bind("<MouseWheel>", self.replot_mouse_wheel)

        self.button_replot_dp = tk.Button(self.root, text="+", command=self.replot_day_p)
        self.button_replot_dp.place(x=x2, y=0, height=h2, width=pts(width_pm), anchor='nw')

        self.button_replot_dm = tk.Button(self.root, text="-", command=self.replot_day_m)
        self.button_replot_dm.place(x=x2, y=h2, height=h2, width=pts(width_pm), anchor='nw')

        self.button_replot_mp = tk.Button(self.root, text="+", command=self.replot_month_p)
        self.button_replot_mp.place(x=x4, y=0, height=h2, width=pts(width_pm), anchor='nw')

        self.button_replot_mm = tk.Button(self.root, text="-", command=self.replot_month_m)
        self.button_replot_mm.place(x=x4, y=h2, height=h2, width=pts(width_pm), anchor='nw')

        self.button_replot_yp = tk.Button(self.root, text="+", command=self.replot_year_p)
        self.button_replot_yp.place(x=x6, y=0, height=h2, width=pts(width_pm), anchor='nw')

        self.button_replot_ym = tk.Button(self.root, text="-", command=self.replot_year_m)
        self.button_replot_ym.place(x=x6, y=h2, height=h2, width=pts(width_pm), anchor='nw')

        self.button_fontsize_p = tk.Button(self.root, text="S+", command=self.new_fontlarger)
        self.button_fontsize_p.place(relx=1, x=pts('-', 3*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_fontsize_m = tk.Button(self.root, text="S–", command=self.new_fontsmaller)
        self.button_fontsize_m.place(relx=1, x=pts('-', 2*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_guisize_p = tk.Button(self.root, text="F+", command=self.new_guilarger, anchor='center')
        self.button_guisize_p.place(relx=1, x=pts('-', 1*width_vw), y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.button_guisize_m = tk.Button(self.root, text="F–", command=self.new_guismaller)
        self.button_guisize_m.place(relx=1, x=0, y=0, height=h1, width=pts(width_vw), anchor='ne')

        self.elongation_select = [ \
            'Merkur', \
            'Venus', \
            'Erde', \
            'Mars', \
            'Jupiter', \
            'Saturn', \
            'Uranus', \
            'Neptun', \
            'Erdmond', \
        ]
        self.dropdown_elongation_var = tk.StringVar(self.root)
        self.dropdown_elongation_var.set(self.elongation_select[0])
        self.dropdown_elongation = tk.OptionMenu(self.root, self.dropdown_elongation_var, *self.elongation_select, command=self.replot)
        self.dropdown_elongation.place(x=0, rely=1, height=h1, width=pts(width_pl), anchor='sw')
        self.dropdown_elongation["highlightthickness"]=0
        self.dropdown_elongation["bg"]='#000000'
        self.dropdown_elongation["fg"]='#aaaaaa'
        self.dropdown_elongation["activebackground"]='#000000'
        self.dropdown_elongation["activeforeground"]='#aaaaaa'
        self.dropdown_elongation['menu'].config(bg="#000000")
        self.dropdown_elongation['menu'].config(fg="#aaaaaa")

        self.elongation_text = tk.StringVar()
        self.elongation_label = tk.Label(self.root, textvariable=self.elongation_text, bg='#000000', fg='#aaaaaa', anchor='w')
        self.elongation_label.place(x=pts(width_pl), rely=1, height=h1, relwidth=1, width=pts('-', width_pl), anchor='sw')

        self.selection_text = tk.StringVar()
        self.selection_label = tk.Label(self.root, textvariable=self.selection_text, bg='#000000', fg='#aaaaaa', anchor='w')
        self.selection_label.place(x=0, y=h1, height=h1, relwidth=1, anchor='nw')

        self.plot_frame = tk.Frame()
        self.plot_frame.place(x=0, rely=1, y=pts('-', h1), height=pts(self.guisize), width=pts(self.guisize), anchor='sw')
        self.plot_window = Plotcanvas(self, (15,15))

        # clicked widget always focused
        self.root.bind_all("<1>", lambda event:event.widget.focus_set())

        self.replot_date(d, m, y)
        #self.plot_window.calc_orbits()
        self.root.mainloop()

    def replot(self, *args):
        self.set_date_planets()
        self.plot_window.clear()
        self.plot_window.plot()
        self.root.update_idletasks()
        time.sleep(0.01)

    def set_date_planets(self):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())

        for i in range(len(self.all_planets)):
            self.all_planets[i].set_date(dt.datetime(y, m, d, 12, 0, 0))

        for i in range(len(self.all_planets)):
            if self.dropdown_elongation_var.get()==self.all_planets[i].name_de:
                self.elongation_text.set( \
                  "  E={:.1f}°".format(self.calc_elongation(i)) + \
                  "  Lon={:.1f}°".format(self.all_planets[i].lon) + \
                  "  Lat={:.1f}°".format(self.all_planets[i].lat) \
                  )

    def calc_elongation(self, planet_index, *args):
        # für Erde mach Elongation keinen Sinn
        if planet_index==2:
            return 0
        else:
            [x1, y1] = pol2cart(self.all_planets[2].rad, self.all_planets[2].lon)
            [x2, y2] = pol2cart(self.all_planets[planet_index].rad, self.all_planets[planet_index].lon)
            x2 = x2 - x1 # Erde-Planet
            y2 = y2 - y1
            x1 = -x1 # Erde-Sonne
            y1 = -y1
            length_1 = np.sqrt(x1**2 + y1**2)
            length_2 = np.sqrt(x2**2 + y2**2)
            return 180/np.pi * np.arccos((x1*x2 + y1*y2) / (length_1 * length_2))
    
    def replot_elongation_p(self, *args):
        self.replot_elongation(1)

    def replot_elongation_m(self, *args):
        self.replot_elongation(-1)

    def replot_elongation(self, timedir, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        Datum_aktuell = dt.date(y, m, d)
        counter = 0
        for i in range(len(self.all_planets)):
            if self.dropdown_elongation_var.get()==self.all_planets[i].name_de:
                if i==2:
                    return
                old_elong = self.calc_elongation(i)
                old_elong_diff = 0
                timedelta = 0
                daydiff = 0
                old_daydiff = 0
                while True:
                    new_date = Datum_aktuell + dt.timedelta(timedelta)
                    self.all_planets[2].set_date(dt.datetime(new_date.year, new_date.month, new_date.day, 12, 0, 0))
                    self.all_planets[i].set_date(dt.datetime(new_date.year, new_date.month, new_date.day, 12, 0, 0))
                    new_elong = self.calc_elongation(i)
                    new_elong_diff = new_elong - old_elong
                    if abs(timedelta) > 1 and daydiff == 1 and old_daydiff == 1: # mindestens zwei ein-Tages-Schritte vollzogen
                        if i < 2:
                            if not np.sign(new_elong_diff) == np.sign(old_elong_diff) and new_elong > 15:
                                new_date = Datum_aktuell + dt.timedelta(timedelta-timedir/abs(timedir))
                                self.replot_date(new_date.day, new_date.month, new_date.year)
                                print("Found elongation after " + str(counter) + " steps.")
                                return
                        if i > 2:
                            if not np.sign(new_elong_diff) == np.sign(old_elong_diff) and new_elong > 170:
                                new_date = Datum_aktuell + dt.timedelta(timedelta-timedir/abs(timedir))
                                self.replot_date(new_date.day, new_date.month, new_date.year)
                                print("Found elongation after " + str(counter) + " steps.")
                                return
                    if timedelta > 1e4:
                        print("Did not find elongation after " + str(counter) + " steps.")
                        return                        
                    old_elong = new_elong
                    old_elong_diff = new_elong_diff
                    if i > 2:
                        if new_elong_diff < 0:
                            # Nimmt die Elongation noch ab kann man schneller springen
                            daydiff = 30
                        else:
                            # Nimmt die Elongation zu muss man umso langsamer werden je näher an 180
                            daydiff = int(abs(new_elong - 180) / 2) + 1
                    elif i == 1:
                        if new_elong > 2 and new_elong_diff < 0 and daydiff == 1:
                            # Nimmt die Elongation nach Abendsicht wieder ab (die Venus ist uns noch hinterher) dauert es etwas mehr als einen halben Venus-Umlauf bis zur Morgensicht
                            # Nimmt die Elongation nach Morgensicht wieder ab (die Venus ist uns voraus) dauert es ziemlich genau zwei Venus-Umläufe bis zur Abendsicht
                            if timedir > 0:
                                jumpfac_1 = 1.5
                                jumpfac_2 = 0.4
                            else:
                                jumpfac_1 = 0.4
                                jumpfac_2 = 1.5
                            planet_lon = self.all_planets[i].lon
                            earth_lon = self.all_planets[2].lon
                            if earth_lon < 180:
                                if planet_lon > earth_lon and planet_lon < earth_lon + 180:
                                    daydiff = int(225 * jumpfac_1)
                                else:
                                    daydiff = int(225 * jumpfac_2)
                            else:
                                if planet_lon > earth_lon or planet_lon < earth_lon - 180:
                                    daydiff = int(225 * jumpfac_1)
                                else:
                                    daydiff = int(225 * jumpfac_2)
                        elif new_elong < 40:
                            daydiff = 5
                        else:
                            daydiff = 1
                    elif i == 0:
                        if new_elong > 2 and new_elong_diff < 0 and daydiff == 1:
                            # Nimmt die Elongation nach Abendsicht wieder ab (der Merkur ist uns noch hinterher) dauert es ziemlich genau einen halben Merkur-Umlauf bis zur Morgensicht
                            # Nimmt die Elongation nach Morgensicht wieder ab (der Merkur ist uns voraus) dauert es ungefähr einen dreiviertel Merkur-Umlauf bis zur Abendsicht
                            if timedir > 0:
                                jumpfac_1 = 0.4
                                jumpfac_2 = 0.2
                            else:
                                jumpfac_1 = 0.2
                                jumpfac_2 = 0.4
                            planet_lon = self.all_planets[i].lon
                            earth_lon = self.all_planets[2].lon
                            if earth_lon < 180:
                                if planet_lon > earth_lon and planet_lon < earth_lon + 180:
                                    daydiff = int(88 * jumpfac_1)
                                else:
                                    daydiff = int(88 * jumpfac_2)
                            else:
                                if planet_lon > earth_lon or planet_lon < earth_lon - 180:
                                    daydiff = int(88 * jumpfac_1)
                                else:
                                    daydiff = int(88 * jumpfac_2)
                        elif new_elong < 15:
                            daydiff = 3
                        else:
                            daydiff = 1
                    else:
                        daydiff = 1
                    if timedir > 0:
                        timedelta += daydiff
                    else:
                        timedelta -= daydiff
                    old_daydiff = daydiff
                    counter += 1                
                
    def replot_date(self, d, m, y, *args):
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(d))
        self.entry_2.insert("0",str(m))
        self.entry_3.insert("0",str(y))
        self.replot()

    def replot_today(self, *args):
        new_date = dt.date.today()
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(new_date.day))
        self.entry_2.insert("0",str(new_date.month))
        self.entry_3.insert("0",str(new_date.year))
        self.replot()

    def replot_2000(self, *args):
        new_date = dt.date.today()
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0","1")
        self.entry_2.insert("0","1")
        self.entry_3.insert("0","2000")
        self.replot()

    def switch_view(self, *event):
        self.view_mode = (self.view_mode + 1) % 7
        self.replot()

    def switch_view_rev(self, *event):
        self.view_mode = (self.view_mode - 1 + 7) % 7
        self.replot()

    def switch_fix_earth(self, *event):
        self.fix_earth = (self.fix_earth + 1) % 2
        self.replot()

    def replot_p(self, *args):
        current_focus = self.root.focus_get()
        if not (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            self.replot_day_p()

    def replot_m(self, *args):
        current_focus = self.root.focus_get()
        if not (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            self.replot_day_m()

    def replot_strg_p(self, *args):
        current_focus = self.root.focus_get()
        if not (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            self.replot_3days_p()

    def replot_strg_m(self, *args):
        current_focus = self.root.focus_get()
        if not (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            self.replot_3days_m()

    def replot_day_p(self, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        Datum_aktuell = dt.date(y, m, d)
        new_date = Datum_aktuell + dt.timedelta(1)
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(new_date.day))
        self.entry_2.insert("0",str(new_date.month))
        self.entry_3.insert("0",str(new_date.year))
        #self.root.after(10, self.replot())
        self.replot()
        
    def replot_day_m(self, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        Datum_aktuell = dt.date(y, m, d)
        new_date = Datum_aktuell + dt.timedelta(-1)
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(new_date.day))
        self.entry_2.insert("0",str(new_date.month))
        self.entry_3.insert("0",str(new_date.year))
        self.replot()

    def replot_3days_p(self, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        Datum_aktuell = dt.date(y, m, d)
        new_date = Datum_aktuell + dt.timedelta(3)
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(new_date.day))
        self.entry_2.insert("0",str(new_date.month))
        self.entry_3.insert("0",str(new_date.year))
        #self.root.after(10, self.replot())
        self.replot()
        
    def replot_3days_m(self, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        Datum_aktuell = dt.date(y, m, d)
        new_date = Datum_aktuell + dt.timedelta(-3)
        self.entry_1.delete(0, 'end')
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_1.insert("0",str(new_date.day))
        self.entry_2.insert("0",str(new_date.month))
        self.entry_3.insert("0",str(new_date.year))
        self.replot()

    def replot_month_p(self, *args):
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        if m==12:
            new_m = 1
            new_y = y + 1
        else:
            new_m = m + 1
            new_y = y
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_2.insert("0",str(new_m))
        self.entry_3.insert("0",str(new_y))
        self.replot()

    def replot_month_m(self, *args):
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        if m==1:
            new_m = 12
            new_y = y - 1
        else:
            new_m = m - 1
            new_y = y
        self.entry_2.delete(0, 'end')
        self.entry_3.delete(0, 'end')
        self.entry_2.insert("0",str(new_m))
        self.entry_3.insert("0",str(new_y))
        self.replot()

    def replot_year_p(self, *args):
        y = int(self.entry_3.get())
        self.entry_3.delete(0, 'end')
        self.entry_3.insert("0",str(y+1))
        self.replot()

    def replot_year_m(self, *args):
        y = int(self.entry_3.get())
        self.entry_3.delete(0, 'end')
        self.entry_3.insert("0",str(y-1))
        self.replot()

    def replot_century_p(self, *args):
        y = int(self.entry_3.get())
        self.entry_3.delete(0, 'end')
        self.entry_3.insert("0",str(y+100))
        self.replot()

    def replot_century_m(self, *args):
        y = int(self.entry_3.get())
        self.entry_3.delete(0, 'end')
        self.entry_3.insert("0",str(y-100))
        self.replot()

    def replot_mouse_wheel(self, event, *args):
        current_focus = self.root.focus_get()
        if current_focus == self.entry_1:
            if event.num == 5 or event.delta == -120:
                self.replot_day_p()
            if event.num == 4 or event.delta == 120:
                self.replot_day_m()
        elif current_focus == self.entry_2:
            if event.num == 5 or event.delta == -120:
                self.replot_month_p()
            if event.num == 4 or event.delta == 120:
                self.replot_month_m()
        elif current_focus == self.entry_3:
            if event.num == 5 or event.delta == -120:
                self.replot_year_p()
            if event.num == 4 or event.delta == 120:
                self.replot_year_m()
        else:
            if event.num == 5 or event.delta == -120:
                self.replot_day_p()
            if event.num == 4 or event.delta == 120:
                self.replot_day_m()
        
    def switch_elongation_selection(self, *args):
        if self.dropdown_elongation_var.get()==self.elongation_select[len(self.elongation_select)-1]:
            self.dropdown_elongation_var.set(self.elongation_select[0])
            self.replot()
            return
        else:
            for i in range(len(self.elongation_select)):
                if self.dropdown_elongation_var.get()==self.elongation_select[i]:
                    self.dropdown_elongation_var.set(self.elongation_select[i+1])
                    self.replot()
                    return

    def switch_elongation_selection_rev(self, *args):
        if self.dropdown_elongation_var.get()==self.elongation_select[0]:
            self.dropdown_elongation_var.set(self.elongation_select[len(self.elongation_select)-1])
            self.replot()
            return
        else:
            for i in range(len(self.elongation_select)):
                if self.dropdown_elongation_var.get()==self.elongation_select[i]:
                    self.dropdown_elongation_var.set(self.elongation_select[i-1])
                    self.replot()
                    return

    def new_guilarger(self, *args):
        # get old date
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        # get old position
        geostring = self.root.geometry()
        pluspos = geostring.find("+")
        posstring = geostring[pluspos+1:len(geostring)]
        pluspos = posstring.find("+")
        xpos = int(posstring[0:pluspos])
        dxpos = int(self.root.winfo_fpixels(pts(30)))
        ypos = int(posstring[pluspos+1:len(posstring)])
        # destroy this instance and create new
        self.root.destroy()
        NewGUI(self.guisize + 30, self.fontsize, xpos - dxpos, ypos, d, m, y)

    def new_guismaller(self, *args):
        # safety: plus-button should be visible afterwards
        if self.guisize - 30 < 3*self.button_guisize_m.winfo_width():
            return
        # get old date
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        # get old position
        geostring = self.root.geometry()
        pluspos = geostring.find("+")
        posstring = geostring[pluspos+1:len(geostring)]
        pluspos = posstring.find("+")
        xpos  = int(posstring[0:pluspos])
        dxpos = int(self.root.winfo_fpixels(pts(30)))
        ypos  = int(posstring[pluspos+1:len(posstring)])
        # destroy this instance and create new
        self.root.destroy()
        NewGUI(self.guisize - 30, self.fontsize, xpos + dxpos, ypos, d, m, y)

    def new_fontlarger(self, *args):
        # get old date
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        # get old position
        geostring = self.root.geometry()
        pluspos = geostring.find("+")
        posstring = geostring[pluspos+1:len(geostring)]
        pluspos = posstring.find("+")
        xpos = int(posstring[0:pluspos])
        ypos = int(posstring[pluspos+1:len(posstring)])
        # destroy this instance and create new
        self.root.destroy()
        NewGUI(self.guisize, self.fontsize + 1, xpos, ypos, d, m, y)

    def new_fontsmaller(self, *args):
        # safety: font not negative
        if self.fontsize == 1:
            return
        # get old date
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        # get old position
        geostring = self.root.geometry()
        pluspos = geostring.find("+")
        posstring = geostring[pluspos+1:len(geostring)]
        pluspos = posstring.find("+")
        xpos = int(posstring[0:pluspos])
        ypos = int(posstring[pluspos+1:len(posstring)])
        # destroy this instance and create new
        self.root.destroy()
        NewGUI(self.guisize, self.fontsize - 1, xpos, ypos, d, m, y)

    def on_close(self):
        with open("Sonnensystem.conf", "w") as conf:
            conf.write(self.root.geometry() + '#' + str(self.guisize) + '#' + str(self.fontsize))
        self.root.destroy()






# ----------------------------------------------
# CLASS PLOTCANVAS
# ----------------------------------------------
class Plotcanvas():
    def __init__(self, root, size):
        self.root = root
        self.fig = mpl.figure.Figure(size, constrained_layout=True)
        self.fig.patch.set_facecolor('#000000')
        self.ax = self.fig.add_subplot(111)
        self.canvas = tkcairo.FigureCanvasTkCairo(self.fig, master=root.plot_frame)
        self.canvas.get_tk_widget().pack()
        self.plat  = np.zeros(9)
        self.plon  = np.zeros(9)
        self.pdist = np.zeros(9)
        self.px = np.zeros(9)
        self.py = np.zeros(9)
        self.pz = np.zeros(9)
        self.olat = []
        self.olon = []
        self.odist = []
        self.ox = []
        self.oy = []
        self.oz = []
        nr_steps = 200
        for i in range(9):
            self.plon[i] = self.root.all_planets[i].perihel
            self.pdist[i] = self.root.all_planets[i].periheldist
            [self.px[i], self.py[i]] = pol2cart(self.pdist[i], self.plon[i])
            self.olat.append(np.zeros(nr_steps))
            self.olon.append(np.zeros(nr_steps))
            self.odist.append(np.zeros(nr_steps))
            self.ox.append(np.zeros(nr_steps))
            self.oy.append(np.zeros(nr_steps))
            self.oz.append(np.zeros(nr_steps))
            for n in range(nr_steps):
                self.olat[i][n] = 0
                self.olon[i][n] = n/(nr_steps-1) * 360 + self.root.all_planets[i].perihel + 180
                self.odist[i][n] = self.root.all_planets[i].p / (1 - self.root.all_planets[i].excen * np.cos(n/(nr_steps-1) * 2*np.pi))
                [self.ox[i][n], self.oy[i][n]] = pol2cart(self.odist[i][n], self.olon[i][n])
                self.oz[i][n] = np.sin(np.pi/180*(self.olon[i][n] - self.root.all_planets[i].aufstkn))

    def calc_orbits(self):

        # Not Finished

        self.olat = []
        self.olon = []
        self.odist = []
        self.ox = []
        self.oy = []
        self.oz = []
        for i in range(9):
            nr_steps = 40
            self.olat.append(np.zeros(2*nr_steps))
            self.olon.append(np.zeros(2*nr_steps))
            self.odist.append(np.zeros(2*nr_steps))
            self.ox.append(np.zeros(2*nr_steps))
            self.oy.append(np.zeros(2*nr_steps))
            self.oz.append(np.zeros(2*nr_steps))
            step = self.root.all_planets[i].period / (2*nr_steps-1)
            original_date = dt.datetime(2000,1,1,12,0,0)
            for n in range(2*nr_steps):
                self.root.all_planets[i].set_date(original_date + dt.timedelta((-nr_steps+n)*step))
                self.olat[i][n] = self.root.all_planets[i].lat
                self.olon[i][n] = self.root.all_planets[i].lon
                self.odist[i][n] = self.root.all_planets[i].rad
                self.ox[i][n] = self.root.all_planets[i].x
                self.oy[i][n] = self.root.all_planets[i].y
                self.oz[i][n] = self.root.all_planets[i].z

            # determine perihel positions
            ind = np.argmin(self.odist[i][n])
            close_perihel_distances = np.zeros(2*nr_steps)
            close_perihel_date = original_date + dt.timedelta((-nr_steps+ind)*step)
            step = 2*step / (2*nr_steps-1)
            for n in range(2*nr_steps):
                self.root.all_planets[i].set_date(close_perihel_date + dt.timedelta((-nr_steps+n)*step))
                close_perihel_distances[n] = self.root.all_planets[i].rad
            ind = np.argmin(close_perihel_distances[n])
            close_perihel_date = close_perihel_date + dt.timedelta((-nr_steps+ind)*step)
            self.root.all_planets[i].set_date(close_perihel_date)
            self.plat[i] = self.root.all_planets[i].lat
            self.plon[i] = self.root.all_planets[i].lon
            self.pdist[i] = self.root.all_planets[i].rad
            self.px[i] = self.root.all_planets[i].x
            self.py[i] = self.root.all_planets[i].y
            self.pz[i] = self.root.all_planets[i].z
            self.root.all_planets[i].set_date(original_date)

    def clear(self):
        self.ax.cla()
        self.canvas.draw()

    def plot(self):
            
        ###### SET UP ######
        scale = 1.8 * self.root.guisize / 400
        Orbit_pol_lw = scale * 1.0
        Moon_size = 0.07
        Perihel_size = 0.3
        Sun_size = 0.45
        Moon_orbit = 180
        Saturnring_inner = 0.30
        Saturnring_outer = 0.38

        planetsizes = 0.009 * np.array([15, 24, 25, 22, 40, 23, 30, 30])
        planetcolors = np.array([[0.8, 0.6, 0.4], [0.9, 0.8, 0.5], [0.1, 0.5, 1], [0.9, 0.3, 0], [0.9, 0.8, 0.5], [0.8, 0.6, 0.4], [0, 0.7, 0.7], [0, 0.5, 0.9]])


        ###### POSITIONS ######
        x = np.zeros(9)
        y = np.zeros(9)
        ox = np.empty((9, 0)).tolist()
        oy = np.empty((9, 0)).tolist()
        oz = np.empty((9, 0)).tolist()
        px = np.zeros(9)
        py = np.zeros(9)
        pd = np.zeros(9)
        if self.root.view_mode == 0:
            for i in range(8):
                [x[i], y[i]] = pol2cart(i+1, self.root.all_planets[i].lon)
                phi = np.arange(0, 360.1, 1)
                [ox[i], oy[i]] = pol2cart(i+1, phi)
        else:
            for i in range(9):
                x[i] = self.root.all_planets[i].x
                y[i] = self.root.all_planets[i].y
                ox[i] = self.ox[i]
                oy[i] = self.oy[i]
                oz[i] = self.oz[i]
                px[i] = self.px[i]
                py[i] = self.py[i]
                pd[i] = np.sqrt(px[i]**2 + py[i]**2)
        x[8] = self.root.all_planets[8].x - self.root.all_planets[2].x
        y[8] = self.root.all_planets[8].y - self.root.all_planets[2].y

        # select
        if self.root.view_mode == 0:
            view_scale = 1
            planet_indices = range(8)
        elif self.root.view_mode == 1:
            view_scale = 4.8
            planet_indices = [0,1,2,3]
        elif self.root.view_mode == 2:
            view_scale = 1.5
            planet_indices = [2,3,4]
        elif self.root.view_mode == 3:
            view_scale = 0.8
            planet_indices = [2,3,4,5]
        elif self.root.view_mode == 4:
            view_scale = 0.4
            planet_indices = [4,5,6]
        elif self.root.view_mode == 5:
            view_scale = 0.25
            planet_indices = [4,5,6,7]
        else:
            view_scale = 2000
            planet_indices = [2]
    
        # scale
        x = view_scale * x
        y = view_scale * y
        px = view_scale * px
        py = view_scale * py
        pd = view_scale * pd
        for i in range(9):
            ox[i] = [view_scale * n for n in ox[i]]
            oy[i] = [view_scale * n for n in oy[i]]
            oz[i] = [view_scale * n for n in oz[i]]
        Moon_orbit = Moon_orbit / view_scale
        
        # rotate
        if self.root.fix_earth == 1:
            rot_angle = -np.radians(self.root.all_planets[2].lon)
            x_ = x * np.cos(rot_angle) - y * np.sin(rot_angle)
            y_ = x * np.sin(rot_angle) + y * np.cos(rot_angle)
            x = x_
            y = y_
            px_ = px * np.cos(rot_angle) - py * np.sin(rot_angle)
            py_ = px * np.sin(rot_angle) + py * np.cos(rot_angle)
            px = px_
            py = py_
            for i in range(9):
                for n in range(len(ox[i])):
                    ox_ = ox[i][n] * np.cos(rot_angle) - oy[i][n] * np.sin(rot_angle)
                    oy_ = ox[i][n] * np.sin(rot_angle) + oy[i][n] * np.cos(rot_angle)
                    ox[i][n] = ox_
                    oy[i][n] = oy_

        ###### EQUIDISTANT VIEW ######
        if self.root.view_mode == 0:

            # calc and plot planet positions and orbits
            for i in range(8):
                self.ax.plot(ox[i], oy[i], color=[0.3, 0.3, 0.3], linewidth=Orbit_pol_lw, zorder=0)
                self.ax.add_patch(plt.Circle((x[i], y[i]), planetsizes[i], color=planetcolors[i,:], zorder=2))

            # plot sun and saturn rings
            self.ax.add_patch(plt.Circle((0, 0), Sun_size, color=[0.9, 0.8, 0], zorder=1))
            self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_outer, color=planetcolors[5,:], zorder=1))
            self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_inner, color='black', zorder=1))

            # plot moon
            self.ax.add_patch(plt.Circle((x[2] + Moon_orbit * x[8], y[2] + Moon_orbit * y[8]), Moon_size, color=[0.7, 0.7, 0.7]))


        ###### REAL DISTANCES VIEWS ######
        elif self.root.view_mode >= 1 and self.root.view_mode <= 5:

            for i in planet_indices:

                # orbits
                self.ax.plot(ox[i], oy[i], color=[0.25, 0.25, 0.25], linewidth=Orbit_pol_lw, zorder=0)
                if not (i==2):
                    self.ax.plot(select_larger_zero(ox[i], oz[i]), select_larger_zero(oy[i], oz[i]), color=[0.35, 0.35, 0.35], linewidth=Orbit_pol_lw, zorder=0)
                
                # perihels
                self.ax.plot([px[i] * (1 - Perihel_size / pd[i]), px[i]], [py[i] * (1 - Perihel_size / pd[i]), py[i]], color=[0.3, 0.3, 0.3], linewidth=Orbit_pol_lw, zorder=0)
                
                # planets
                self.ax.add_patch(plt.Circle((x[i], y[i]), planetsizes[i], color=planetcolors[i,:], zorder=2))

            # plot sun
            self.ax.add_patch(plt.Circle((0, 0), Sun_size, color=[0.9, 0.8, 0], zorder=1))

            # plot earthline
            self.ax.plot([0, 15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, 15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, zorder=0)
            self.ax.plot([0, -15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, -15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, linestyle='--', zorder=0)

            # plot poles
            for i in planet_indices:
                if i in [2,3,5,6,7]:
                    dx = planetsizes[i] * np.cos(self.root.all_planets[i].pole / 180 * np.pi)
                    dy = planetsizes[i] * np.sin(self.root.all_planets[i].pole / 180 * np.pi)
                    self.ax.plot(\
                        [x[i] + 0.1 * dx, x[i] + dx], \
                        [y[i] + 0.1 * dy, y[i] + dy], \
                        color='black', linewidth=Orbit_pol_lw, zorder=3)

            # plot moon
            if 2 in planet_indices and max(planet_indices) < 4:
                self.ax.add_patch(plt.Circle((x[2] + Moon_orbit * x[8], y[2] + Moon_orbit * y[8]), Moon_size, color=[0.7, 0.7, 0.7]))

            if 5 in planet_indices:
                self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_outer, color=planetcolors[5,:], zorder=1))
                self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_inner, color='black', zorder=1))

        ###### EARTH-MOON VIEW ######
        else:

            # orbit
            self.ax.plot(ox[8], oy[8], color=[0.25, 0.25, 0.25], linewidth=Orbit_pol_lw, zorder=0)

            # planets
            self.ax.add_patch(plt.Circle((0, 0), planetsizes[2], color=planetcolors[2,:], zorder=1))
            self.ax.add_patch(plt.Circle((x[8], y[8]), Moon_size, color=[0.7, 0.7, 0.7], zorder=2))

            # earthline
            self.ax.plot([0, -15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, -15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, zorder=0)
            self.ax.plot([0, 15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, 15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, linestyle='--', zorder=0)


        # GENERAL PLOT SETTINGS AND TEXT

        self.ax.set_xlim(8.5*np.array([-1, 1]))
        self.ax.set_ylim(8.5*np.array([-1, 1]))
        
        self.ax.axis('off')
        
        self.canvas.draw()








# ----------------------------------------------
# CLASS PLANET
# ----------------------------------------------
class Planet():
    def __init__(self, root, name_en, name_de, period, pole, a, excen, perihel, aufstkn):
        self.root = root
        self.name_en = name_en
        self.name_de = name_de
        self.period = period
        self.pole = pole
        self.a = a
        self.excen = excen
        self.e = self.a*self.excen
        self.b = np.sqrt(self.a**2 - self.e**2)
        self.p = self.b**2/self.a
        self.periheldist = self.a * (1 - self.excen)
        self.perihel = perihel
        self.aufstkn = aufstkn
        self.lon = 0
        self.lat = 0
        self.rad = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.date = dt.datetime(2000, 1, 1, 12, 0, 0)

    def set_date(self, datetime):

        self.date = datetime
        t = ap.time.Time(str(datetime.year) + '-' + str(datetime.month) + '-' + str(datetime.day) + ' ' + str(datetime.hour) + ':' + str(datetime.minute) + ':' + str(datetime.second), scale='utc')
        
        ICRS = apc.SkyCoord(apc.get_body_barycentric(self.name_en, t, ephemeris='builtin'), frame='icrs', representation_type='cartesian')
        HME_sph = ICRS.transform_to('heliocentricmeanecliptic')
        self.lon = HME_sph.lon.to(ap.units.deg).value
        self.lat = HME_sph.lat.to(ap.units.deg).value
        self.rad = HME_sph.distance.to(ap.units.au).value

        HME_cart = apc.spherical_to_cartesian(HME_sph.distance, HME_sph.lat, HME_sph.lon)
        self.x = HME_cart[0].to(ap.units.au).value
        self.y = HME_cart[1].to(ap.units.au).value
        self.z = HME_cart[2].to(ap.units.au).value



# ----------------------------------------------
# STARTING CODE
# ----------------------------------------------
if __name__ == '__main__':

    # DpiAwareness
    if 1:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            print("SetProcessDpiAwareness(1) nicht erfolgreich... fahre fort.")

    # read config file
    if os.path.isfile("Sonnensystem.conf"): 
        with open("Sonnensystem.conf", "r") as conf:
            confstring = conf.read()
            pluspos = confstring.find("+")
            hashtagpos = confstring.find("#")
            string_pos = confstring[pluspos+1:hashtagpos]
            pluspos = string_pos.find("+")
            string_settings = confstring[hashtagpos+1:len(confstring)]
            hashtagpos = string_settings.find("#")
            guisize = int(string_settings[0:hashtagpos])
            fontsize = int(string_settings[hashtagpos+1:len(string_settings)])
            xpos = int(string_pos[0:pluspos])
            ypos = int(string_pos[pluspos+1:len(string_pos)])
    else:
        guisize = 200
        fontsize = 9
        xpos = 200
        ypos = 100

    # start application
    new_date = dt.date.today()
    NewGUI(guisize, fontsize, xpos, ypos, new_date.day, new_date.month, new_date.year)

