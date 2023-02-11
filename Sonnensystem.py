global GUI_version; GUI_version = '3.3'

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
from scipy.interpolate import interp1d, CubicSpline
from scipy.optimize import curve_fit

warnings.filterwarnings("ignore")
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

def sph2cart(rho, theta, phi):
    x = np.multiply(rho, np.sin(theta / 180 * np.pi), np.cos(phi / 180 * np.pi))
    y = np.multiply(rho, np.sin(theta / 180 * np.pi), np.sin(phi / 180 * np.pi))
    z = np.multiply(rho, np.cos(theta / 180 * np.pi))
    return (x, y, z)

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

def Kepler(x, P, E, L):
    y = P / (1 + E * np.cos((x-L) / 180 * np.pi))
    return y

def calc_date_perihel(planet, timedir, *args):
    if len(args) > 0:
        thisdate = args[0]
    else:
        thisdate = planet.date
    if timedir > 0:
        thisdate = thisdate + dt.timedelta(1 + planet.period)
    else:
        thisdate = thisdate + dt.timedelta(-1)
    original_date = planet.date
    planet.set_date(thisdate, 0)
    angle_since_peri = (planet.lon + 360 - planet.perihel) % 360
    days_since_perihel = (angle_since_peri / 360 * planet.period) % planet.period
    planet.set_date(original_date, 0)
    return thisdate - dt.timedelta(days_since_perihel)

# ----------------------------------------------
# CLASS NEWGUI
# ----------------------------------------------
class NewGUI():

    # guisize and fontsize in points, xpos and ypos in pixels!!
    def __init__(self, guisize, fontsize, xpos, ypos):

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
        self.root.bind('<p>',  self.replot_perihel_p)
        self.root.bind('<Control-p>',  self.replot_perihel_m)
        #self.root.bind("<KeyPress-Right>", self.replot_step)
        #self.root.bind("<KeyRelease-Right>", self.replot_stop)

        # PLANETEN
        # https://de.wikipedia.org/wiki/Liste_der_Planeten_des_Sonnensystems
        today = dt.date.today()
        date_init = dt.datetime(today.year, today.month, today.day, 12, 0, 0)
        self.all_planets = []
        #                                                                      Periode   Pol          a     Exzen    Perihel     aufstKn
        self.all_planets.append(Planet(self, date_init, 'mercury', 'Merkur',  87.96926,  315,   0.38710,  0.20563,  77.45645,   48.33167 ))
        self.all_planets.append(Planet(self, date_init, 'venus',   'Venus',   224.7008,  342,   0.72333,  0.00677, 131.53298,   76.68063 ))
        self.all_planets.append(Planet(self, date_init, 'earth',   'Erde',    365.2564,   90,   1.00000,  0.01671, 102.94719,  -11.26064 ))
        self.all_planets.append(Planet(self, date_init, 'mars',    'Mars',    686.9796,  335,   1.52366,  0.09341, 336.04084,   49.57854 ))
        self.all_planets.append(Planet(self, date_init, 'jupiter', 'Jupiter', 4332.820,  183,   5.20336,  0.04837,  14.75385,  100.55615 ))
        self.all_planets.append(Planet(self, date_init, 'saturn',  'Saturn',  10755.70,   78,   9.53707,  0.05415,  92.43194,  113.71504 ))
        self.all_planets.append(Planet(self, date_init, 'uranus',  'Uranus',  30687.15,   78,  19.19126,  0.04716, 170.96424,   74.22988 ))
        self.all_planets.append(Planet(self, date_init, 'neptune', 'Neptun',  60190.03,  327,  30.06896,  0.00858,  44.97135,  131.72169 ))
        self.all_planets.append(Planet(self, date_init, 'moon', 'Erdmond', 27.3217, 0, 0.00257, 0, 0, 0, self.all_planets[2] ))

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
        self.entry_1.insert("0",str(date_init.day))
        self.entry_1.bind('<Up>', self.replot_day_p)
        self.entry_1.bind('<Down>', self.replot_day_m)
        self.entry_1.bind('<Control-Up>', self.replot_3days_p)
        self.entry_1.bind('<Control-Down>', self.replot_3days_m)

        self.entry_2 = tk.Entry(self.root, justify='center')
        self.entry_2.place(x=x3, y=0, height=h1, width=pts(width_dm), anchor='nw')
        self.entry_2.insert("0",str(date_init.month))
        self.entry_2.bind('<Up>', self.replot_month_p)
        self.entry_2.bind('<Down>', self.replot_month_m)

        self.entry_3 = tk.Entry(self.root, justify='center')
        self.entry_3.place(x=x5, y=0, height=h1, width=pts(width_yr), anchor='nw')
        self.entry_3.insert("0",str(date_init.year))
        self.entry_3.bind('<Up>', self.replot_year_p)
        self.entry_3.bind('<Down>', self.replot_year_m)
        self.entry_3.bind('<Control-Up>', self.replot_century_p)
        self.entry_3.bind('<Control-Down>', self.replot_century_m)

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

        self.replot()
        self.root.mainloop()

    def replot(self, *args):
        d = int(self.entry_1.get())
        m = int(self.entry_2.get())
        y = int(self.entry_3.get())
        self.plot_window.plot(dt.datetime(y, m, d, 12, 0, 0), self.view_mode, self.fix_earth)
        for i in range(9):
            if self.dropdown_elongation_var.get()==self.all_planets[i].name_de:
                self.elongation_text.set( \
                   " E="   + "{:.1f}°".format(self.calc_elongation(i)).rjust(6).replace(" ", "  ") + \
                  "  Lon=" + "{:.1f}°".format(self.all_planets[i].lon).rjust(6).replace(" ", "  ") + \
                  "  Lat=" + "{:.1f}°".format(self.all_planets[i].lat).rjust(5).replace(" ", "  ") \
                  )
        self.root.update_idletasks()
        time.sleep(0.01)

    def calc_elongation(self, planet_index, *args):
        # für Erde mach Elongation keinen Sinn
        if planet_index == 2:
            return 0
        if planet_index == 8:
            lon_m = self.all_planets[8].lon
            lon_e = (self.all_planets[2].lon + 180) % 360
            diff = (lon_m - lon_e + 360) % 360
            if diff > 180:
                return 360 - diff
            else:
                return diff
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
        start_time = time.perf_counter()
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
                    self.all_planets[2].set_date(dt.datetime(new_date.year, new_date.month, new_date.day, 12, 0, 0), 0)
                    self.all_planets[i].set_date(dt.datetime(new_date.year, new_date.month, new_date.day, 12, 0, 0), 0)
                    new_elong = self.calc_elongation(i)
                    new_elong_diff = new_elong - old_elong
                    if abs(timedelta) > 1 and daydiff == 1 and old_daydiff == 1: # mindestens zwei ein-Tages-Schritte vollzogen
                        if i < 2:
                            if not np.sign(new_elong_diff) == np.sign(old_elong_diff) and new_elong > 15:
                                new_date = Datum_aktuell + dt.timedelta(timedelta-timedir/abs(timedir))
                                self.replot_date(new_date.day, new_date.month, new_date.year)
                                break
                        if i > 2:
                            if not np.sign(new_elong_diff) == np.sign(old_elong_diff) and new_elong > 120:
                                new_date = Datum_aktuell + dt.timedelta(timedelta-timedir/abs(timedir))
                                self.replot_date(new_date.day, new_date.month, new_date.year)
                                break
                    if timedelta > 1e4:
                        print("Could not find elongation after " + str(counter) + " steps.")
                        return                        
                    old_elong = new_elong
                    old_elong_diff = new_elong_diff
                    if i == 8:
                        if new_elong_diff < 0:
                            # Nimmt die Elongation noch ab kann man schneller springen
                            daydiff = 5
                        else:
                            # Nimmt die Elongation zu muss man umso langsamer werden je näher an 180
                            daydiff = 1
                    elif i > 2:
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
                    
                # measure time and print
                end_time = time.perf_counter()
                print("Found elongation after " + str(counter) + " steps (" + "{:.1f}".format((end_time-start_time)*1000) + " ms).")

    def replot_perihel_p(self, *args):
        self.replot_perihel(1)

    def replot_perihel_m(self, *args):
        self.replot_perihel(-1)

    def replot_perihel(self, timedir, *args):
        for i in range(len(self.all_planets)):
            if self.dropdown_elongation_var.get()==self.all_planets[i].name_de:
                perihel_date = calc_date_perihel(self.all_planets[i], timedir)
                self.replot_date(perihel_date.day, perihel_date.month, perihel_date.year)
                return

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
        current_focus = self.root.focus_get()
        if (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            return
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
        current_focus = self.root.focus_get()
        if (current_focus == self.entry_1 or current_focus == self.entry_2 or current_focus == self.entry_3):
            return
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
        self.ax.set_xlim(8.5*np.array([-1, 1]))
        self.ax.set_ylim(8.5*np.array([-1, 1]))        
        self.ax.axis('off')
        self.canvas = tkcairo.FigureCanvasTkCairo(self.fig, master=root.plot_frame)
        self.canvas.get_tk_widget().pack()
        self.view_mode = -1
        self.fix_earth = -1

    def clear(self, clear_orbits):
        self.ax.patches = []
        if clear_orbits:
            self.ax.lines = []
        else:
            # Entferne nur farbige (Erde) oder schwarze (Pole) Linien
            to_be_removed = []
            lines = self.ax.lines
            for line in lines:
                thiscolor = line.get_color()
                thiscolor = mpl.colors.to_rgb(thiscolor)
                if not (thiscolor[0] == thiscolor[1] and thiscolor[1] == thiscolor[2]) or thiscolor[0] == 0:
                    to_be_removed.append(1)
                else:
                    to_be_removed.append(0)
            for i in range(len(to_be_removed)-1,0,-1):
                if to_be_removed[i] == 1:
                    lines[i].remove()
    
    def draw(self):
        self.canvas.draw()

    def plot(self, datetime, view_mode, fix_earth):        
        start_time = time.perf_counter()
        if not (view_mode == self.view_mode and fix_earth == self.fix_earth):
            view_changed = True
            print("view changed")
        else:
            view_changed = False
        self.view_mode = view_mode
        self.fix_earth = fix_earth
        
        ###### SET UP ######
        scale = 1.8 * self.root.guisize / 400
        Orbit_pol_lw = scale * 1.0
        Moon_size = 0.07
        Perihel_size = 0.3
        Sun_size = 0.45
        Moon_orbit = 0.5
        Saturnring_inner = 0.30
        Saturnring_outer = 0.38

        planetsizes = 0.009 * np.array([15, 24, 25, 22, 40, 23, 30, 30])
        planetcolors = np.array([[0.8, 0.6, 0.4], [0.9, 0.8, 0.5], [0.1, 0.5, 1], [0.9, 0.3, 0], [0.9, 0.8, 0.5], [0.8, 0.6, 0.4], [0, 0.7, 0.7], [0, 0.5, 0.9]])

        # select
        if view_mode == 0:
            view_scale = 1
            planet_indices = range(9)
        elif view_mode == 1:
            view_scale = 4.8
            planet_indices = [0,1,2,3,8]
        elif view_mode == 2:
            view_scale = 1.5
            planet_indices = [2,3,4]
        elif view_mode == 3:
            view_scale = 0.8
            planet_indices = [2,3,4,5]
        elif view_mode == 4:
            view_scale = 0.4
            planet_indices = [4,5,6]
        elif view_mode == 5:
            view_scale = 0.25
            planet_indices = [4,5,6,7]
        else:
            view_scale = 2000
            planet_indices = [2,8]

        ###### UPDATE PLANETS ########
        if 2 in planet_indices:
            calc_list = planet_indices
        else:
            calc_list = [2]
            calc_list.extend(planet_indices)
        time_pos = 0
        time_orb = 0
        for i in calc_list:
            if not view_changed and view_mode == 0 or (view_mode < 6 and i == 8):
                [orb_flag_, pos_, orb_] = self.root.all_planets[i].set_date(datetime, 0)
            else:
                [orb_flag_, pos_, orb_] = self.root.all_planets[i].set_date(datetime, 1)
            time_pos += pos_
            time_orb += orb_
            if orb_flag_ == True:
                view_changed = True

        pre_time = time.perf_counter()

        ###### POSITIONS AND ORBITS ######
        x = np.zeros(9)
        y = np.zeros(9)
        ox = np.empty((9, 0)).tolist()
        oy = np.empty((9, 0)).tolist()
        oz = np.empty((9, 0)).tolist()
        px = np.zeros(9)
        py = np.zeros(9)
        pdist = np.zeros(9)
        pole = np.zeros(9)
        if view_mode == 0:
            for i in planet_indices:
                if i == 8:
                    [x[i], y[i]] = pol2cart(1, self.root.all_planets[i].lon)
                else:
                    [x[i], y[i]] = pol2cart(i+1, self.root.all_planets[i].lon)
                phi = np.arange(0, 360.1, 1)
                [ox[i], oy[i]] = pol2cart(i+1, phi)
        else:
            for i in calc_list:
                x[i]  = self.root.all_planets[i].x
                y[i]  = self.root.all_planets[i].y
                ox[i] = self.root.all_planets[i].orbit.ox
                oy[i] = self.root.all_planets[i].orbit.oy
                oz[i] = self.root.all_planets[i].orbit.oz
                px[i] = self.root.all_planets[i].orbit.px
                py[i] = self.root.all_planets[i].orbit.py
                pdist[i] = self.root.all_planets[i].orbit.pdist
                pole[i] = self.root.all_planets[i].pole
            
        # scale
        x = view_scale * x
        y = view_scale * y
        px = view_scale * px
        py = view_scale * py
        pdist = view_scale * pdist
        for i in calc_list:
            ox[i] = view_scale * np.array(ox[i])
            oy[i] = view_scale * np.array(oy[i])
            oz[i] = view_scale * np.array(oz[i])

        # rotate
        if self.root.fix_earth == 1:
            view_changed = True # in order to clear orbits
            rot_angle = -np.radians(self.root.all_planets[2].lon)
            x_ = x * np.cos(rot_angle) - y * np.sin(rot_angle)
            y_ = x * np.sin(rot_angle) + y * np.cos(rot_angle)
            x = x_
            y = y_
            px_ = px * np.cos(rot_angle) - py * np.sin(rot_angle)
            py_ = px * np.sin(rot_angle) + py * np.cos(rot_angle)
            px = px_
            py = py_
            for i in calc_list:
                for n in range(len(ox[i])):
                    ox_ = ox[i][n] * np.cos(rot_angle) - oy[i][n] * np.sin(rot_angle)
                    oy_ = ox[i][n] * np.sin(rot_angle) + oy[i][n] * np.cos(rot_angle)
                    ox[i][n] = ox_
                    oy[i][n] = oy_
                pole[i] = pole[i] - self.root.all_planets[2].lon

        calc_time = time.perf_counter()

        ########## CLEAR ##########
        self.clear(view_changed)
        clr_time = time.perf_counter()

        ###### EQUIDISTANT VIEW ######
        if view_mode == 0:
            
            # calc and plot planet positions and orbits
            for i in range(8):
                if view_changed:
                    self.ax.plot(ox[i], oy[i], color=[0.3, 0.3, 0.3], linewidth=Orbit_pol_lw, zorder=0)
                self.ax.add_patch(plt.Circle((x[i], y[i]), planetsizes[i], color=planetcolors[i,:], zorder=2))

            # plot sun and saturn rings
            self.ax.add_patch(plt.Circle((0, 0), Sun_size, color=[0.9, 0.8, 0], zorder=1))
            self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_outer, color=planetcolors[5,:], zorder=1))
            self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_inner, color='black', zorder=1))

            # plot moon
            self.ax.add_patch(plt.Circle(( \
                x[2] + Moon_orbit * x[8] / np.sqrt(x[8]**2 + y[8]**2), \
                y[2] + Moon_orbit * y[8] / np.sqrt(x[8]**2 + y[8]**2)), Moon_size, color=[0.7, 0.7, 0.7]))


        ###### REAL DISTANCES VIEWS ######
        elif view_mode >= 1 and view_mode <= 5:

            for i in planet_indices:
                
                if i==8:
                    continue

                # orbits
                if view_changed:
                    self.ax.plot(ox[i], oy[i], color=[0.25, 0.25, 0.25], linewidth=Orbit_pol_lw, zorder=0)
                    if not (i==2):
                        self.ax.plot(select_larger_zero(ox[i], oz[i]), select_larger_zero(oy[i], oz[i]), color=[0.35, 0.35, 0.35], linewidth=Orbit_pol_lw, zorder=0)

                # perihels
                if view_changed:
                    self.ax.plot([px[i] * (1 - Perihel_size / pdist[i]), px[i]], [py[i] * (1 - Perihel_size / pdist[i]), py[i]], color=[0.3, 0.3, 0.3], linewidth=Orbit_pol_lw, zorder=0)
                
                # planets
                self.ax.add_patch(plt.Circle((x[i], y[i]), planetsizes[i], color=planetcolors[i,:], zorder=2))

            # plot sun
            self.ax.add_patch(plt.Circle((0, 0), Sun_size, color=[0.9, 0.8, 0], zorder=1))

            # plot earthline
            self.ax.plot([0,  15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0,  15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, zorder=0)
            self.ax.plot([0, -15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, -15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, linestyle='--', zorder=0)

            # plot poles
            for i in planet_indices:
                if i in [2,3,5,6,7]:
                    dx = planetsizes[i] * np.cos(pole[i] / 180 * np.pi)
                    dy = planetsizes[i] * np.sin(pole[i] / 180 * np.pi)
                    self.ax.plot(\
                        [x[i] + 0.1 * dx, x[i] + dx], \
                        [y[i] + 0.1 * dy, y[i] + dy], \
                        color='black', linewidth=Orbit_pol_lw, zorder=3)

            # plot moon
            if 2 in planet_indices:
                self.ax.add_patch(plt.Circle(( \
                    x[2] + Moon_orbit * x[8] / np.sqrt(x[8]**2 + y[8]**2), \
                    y[2] + Moon_orbit * y[8] / np.sqrt(x[8]**2 + y[8]**2)) , Moon_size, color=[0.7, 0.7, 0.7]))

            if 5 in planet_indices:
                self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_outer, color=planetcolors[5,:], zorder=1))
                self.ax.add_patch(plt.Circle((x[5], y[5]), Saturnring_inner, color='black', zorder=1))

        ###### EARTH-MOON VIEW ######
        else:

            # orbit
            if view_changed:
                self.ax.plot(ox[8], oy[8], color=[0.25, 0.25, 0.25], linewidth=Orbit_pol_lw, zorder=0)

            # planets
            self.ax.add_patch(plt.Circle((0, 0), planetsizes[2], color=planetcolors[2,:], zorder=1))
            self.ax.add_patch(plt.Circle((x[8], y[8]), Moon_size, color=[0.7, 0.7, 0.7], zorder=2))

            # perihel
            if view_changed:
                self.ax.plot([px[8] * (1 - Perihel_size / pdist[8]), px[8]], [py[8] * (1 - Perihel_size / pdist[8]), py[8]], color=[0.3, 0.3, 0.3], linewidth=Orbit_pol_lw, zorder=0)

            # earthline
            self.ax.plot([0, -15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, -15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, zorder=0)
            self.ax.plot([0, 15*x[2]/np.sqrt(x[2]**2 + y[2]**2)], [0, 15*y[2]/np.sqrt(x[2]**2 + y[2]**2)], color=0.4*planetcolors[2,:], linewidth=Orbit_pol_lw, linestyle='--', zorder=0)

        # DRAW
        self.draw()
        
        # measure time and print
        end_time = time.perf_counter()
        print("Plotted in " + "{:.0f}".format((end_time-start_time)*1000).rjust(4) + " ms: " \
              + "pos " + "{:.0f}".format(time_pos).rjust(3) + ", " \
              + "orb " + "{:.0f}".format(time_orb).rjust(3) + ", " \
              + "calc " + "{:.0f}".format((calc_time-pre_time)*1000).rjust(3) + ", " \
              + "clr " + "{:.0f}".format((clr_time-calc_time)*1000).rjust(3) + ", " \
              + "draw " + "{:.0f}".format((end_time-clr_time)*1000).rjust(3) + ")")









# ----------------------------------------------
# CLASS PLANET
# ----------------------------------------------
class Planet():
    def __init__(self, root, date, name_en, name_de, period, pole, a, excen, perihel, aufstkn, *parent):
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
        self.date = date
        self.calc_date_perihel_J2000 = date
        self.umlaufnr = 0
        if len(parent) > 0:
            self.parent = parent[0]
        else:
            self.parent = []
        
        # update using set_date method
        self.set_date(self.date, 1)
        self.calc_date_perihel_J2000 = calc_date_perihel(self, -1, dt.datetime(2000, 1, 1, 12, 0, 0))
        self.umlaufnr = int((self.date - self.calc_date_perihel_J2000).days/self.period)
        self.orbit = Orbit(self)
        
    def set_date(self, datetime, recalc_orbit):
        start_time = time.perf_counter()
        old_date = self.date
        if datetime == old_date and not recalc_orbit:
            return [False, 0, 0]
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
        
        # mit Parent setze relative Koordinaten
        if self.parent:
            if not self.parent.date == self.date:
                self.parent.set_date(datetime, recalc_orbit)
            self.x = self.x - self.parent.x
            self.y = self.y - self.parent.y
            self.z = self.z - self.parent.z
            [self.rad, self.lat, self.lon] = apc.cartesian_to_spherical(self.x, self.y, self.z)
            self.lat = self.lat.value * 180 / np.pi
            self.lon = self.lon.value * 180 / np.pi
        
        pos_time = time.perf_counter()

        # vergleiche Umlaufnummer, wenn verändert, berechne Orbit neu
        orb_flag_ = False
        if recalc_orbit == 1:
            old_umlaufnr = self.umlaufnr
            self.umlaufnr = int((self.date - self.calc_date_perihel_J2000).days/self.period)
            if not self.umlaufnr == old_umlaufnr:
                self.orbit.calc_precise()
                orb_flag_ = True
        
        orb_time = time.perf_counter()
        return [orb_flag_, (pos_time-start_time)*1000, (orb_time-pos_time)*1000]


# ----------------------------------------------
# CLASS ORBITS
# ----------------------------------------------
class Orbit():
    def __init__(self, root):
        self.root = root
        self.olat = []
        self.olon = []
        self.odist = []
        self.ox = []
        self.oy = []
        self.oz = []
        self.plat  = 0
        self.plon  = 0
        self.pdist = 0
        self.px = 0
        self.py = 0
        self.pz = 0
        self.calc_precise()
    
    def reset(self):
        self.olat = []
        self.olon = []
        self.odist = []
        self.ox = []
        self.oy = []
        self.oz = []
        self.plat  = 0
        self.plon  = 0
        self.pdist = 0
        self.px = 0
        self.py = 0
        self.pz = 0

    def calc_simple(self):
        self.reset()
        nr_steps = 200
        self.plon = self.root.perihel
        self.pdist = self.root.periheldist
        [self.px, self.py] = pol2cart(self.pdist, self.plon)
        for n in range(nr_steps):
            self.olat.append(0)
            self.olon.append(n/(nr_steps-1) * 360 + self.root.perihel + 180)
            self.odist.append(self.root.p / (1 - self.root.excen * np.cos(n/(nr_steps-1) * 2*np.pi)))
            [ox_, oy_] = pol2cart(self.odist[n], self.olon[n])
            self.ox.append(ox_)
            self.oy.append(oy_)
            self.oz.append(np.sin(np.pi/180*(self.olon[n] - self.root.aufstkn)))

    def calc_precise(self):
        start_time = time.perf_counter()
        self.reset()
        nr_steps = 6
        steps = np.linspace(0, self.root.period, nr_steps)
        steps = steps[:-1]
        original_date = self.root.date
        start_date = calc_date_perihel(self.root, -1)
        templat = []
        templon = []
        tempdist = []
        for n in range(len(steps)):
            self.root.set_date(start_date + dt.timedelta(steps[n]), 0)
            templat.append(self.root.lat)
            templon.append(self.root.lon)
            tempdist.append(self.root.rad)
        self.root.set_date(original_date, 0)

        # sort arrays and extend
        sortindices = np.argsort(templon)
        templon = [templon[idx] for idx in sortindices]
        templat = [templat[idx] for idx in sortindices]
        tempdist = [tempdist[idx] for idx in sortindices]
        templon.insert(0, templon[-1]-360)
        templat.insert(0, templat[-1])
        tempdist.insert(0, tempdist[-1])
        templon.append(templon[1]+360)
        templat.append(templat[1])
        tempdist.append(tempdist[1])

        # fit orbit in polar coordinates
        nr_steps_interp = 80
        templon_interp = np.linspace(0, 360, nr_steps_interp)
        # in-plane Kepler-fit
        param, _ = curve_fit(Kepler, templon, tempdist, p0=[self.root.p, self.root.excen, self.root.perihel])
        tempdist_interp = Kepler(templon_interp, param[0], param[1], param[2])
        # latitute polynomial fit
        poly_lat = np.poly1d(np.polyfit(templon, templat,6))
        templat_interp = poly_lat(templon_interp)
        self.olon = templon_interp.tolist()
        self.olat = templat_interp.tolist()
        self.odist = tempdist_interp.tolist()
        
        # set perihel
        self.plat  = 0
        self.plon  = param[2]
        self.pdist = param[0]/(1+param[1])

        # repeat for closed circle
        self.olon.append(self.olon[0])
        self.olat.append(self.olat[0])
        self.odist.append(self.odist[0])

        # calculate cartesian
        [self.ox, self.oy, self.oz] = apc.spherical_to_cartesian(self.odist, np.radians(self.olat), np.radians(self.olon))
        [self.px, self.py, self.pz] = apc.spherical_to_cartesian(self.pdist, np.radians(self.plat), np.radians(self.plon))
        
        # measure time and print
        end_time = time.perf_counter()
        print("calculated orbit of " + self.root.name_en + " in " + "{:.1f}".format((end_time-start_time)*1000) + " ms")

        


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
    NewGUI(guisize, fontsize, xpos, ypos)

