import gi
import math
import time
import threading
import platform
from pynput.mouse import Listener as MouseListener
from pynput import keyboard
import pynput.keyboard as kb
import pynput.mouse as ms


gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk


keys = kb.Controller()
mouse = ms.Controller()
os = platform.system()


YourX = YourY = EnemyX = EnemyY = None
velocity = angle = highVelocity = highAngle = 0
set_wind = 0


def calcVelocity(distancex,distancey,angle):
    g = -379.106
    q = 0.0518718
    v0 = -2/(g * q) * math.sqrt((-g * distancex**2)/(2 * math.cos(math.radians(angle))**2 * (math.tan(math.radians(angle)) * distancex - distancey)))
    return v0

def calcVelocityWithWind(s_x,s_y,angle,wind):
    g = 379.106
    q = 0.0518718
    z = 0.5
    w = z * wind
    v_0 = (g * s_x - w * s_y)/math.sqrt(2 * g * s_x * math.sin(math.radians(angle)) * math.cos(math.radians(angle)) + 2 * g * s_y * math.cos(math.radians(angle))**2 + 2 * w * s_x * math.sin(math.radians(angle))**2 + 2 * w * s_y * math.sin(math.radians(angle)) * math.cos(math.radians(angle)))
    power = (2/(g * q)) * v_0
    return power

def calcOptimal(diffx,diffy,wind):
    global velocity, angle
    smallestVelocity = 100
    bestAngle = 0
    for possibleAngle in range(1, 90):
        try:
            v0 = calcVelocityWithWind(diffx, diffy, possibleAngle, wind) if wind else calcVelocity(diffx, diffy, possibleAngle)
            if v0 < smallestVelocity:
                smallestVelocity = v0
                bestAngle = possibleAngle
        except:
            pass
    velocity = smallestVelocity
    angle = bestAngle

def calcHighestBelow100(diffx, diffy, wind):
    global highVelocity, highAngle
    for possibleAngle in range(1, 90):
        try:
            v0 = calcVelocityWithWind(diffx, diffy, 90 - possibleAngle, wind) if wind else calcVelocity(diffx, diffy, 90 - possibleAngle)
        except:
            v0 = 101
        if v0 < 100:
            break
    highVelocity = v0
    highAngle = 90 - possibleAngle

def setPowerAndAngle(targetPower, targetAngle, startPower, startAngle, direction):
    diffPower = targetPower - startPower
    diffAngle = targetAngle - startAngle if direction == "left" else -targetAngle + startAngle
    key_up, key_down = kb.Key.up, kb.Key.down
    key_left, key_right = kb.Key.left, kb.Key.right

    for _ in range(abs(diffPower)):
        keys.tap(key_up if diffPower > 0 else key_down)
        time.sleep(0.05)
    for _ in range(abs(diffAngle)):
        keys.tap(key_right if diffAngle > 0 else key_left)
        time.sleep(0.05)

def setTo100_90(tankx, tanky):
    mouse.position = (tankx, tanky)
    time.sleep(0.05)
    mouse.press(ms.Button.left)
    time.sleep(0.05)
    mouse.move(0, -tanky)
    time.sleep(0.05)
    mouse.release(ms.Button.left)

def posPlayer(x, y, button, pressed):
    global YourX, YourY
    if pressed:
        YourX, YourY = x, y
        return False

def posEnemy(x, y, button, pressed):
    global EnemyX, EnemyY
    if pressed:
        EnemyX, EnemyY = x, y
        return False


class TankHelper(Gtk.Window):
    def __init__(self):
        super().__init__(title="Shellshock Live Aimer")
        self.set_border_width(15)
        self.set_default_size(400, 250)
        self.set_keep_above(True)  

        grid = Gtk.Grid(column_spacing=12, row_spacing=12, column_homogeneous=True)
        self.add(grid)

        self.wind_entry = Gtk.Entry()
        self.wind_entry.set_placeholder_text("Enter Wind Strength")
        grid.attach(self.wind_entry, 0, 0, 2, 1)

        btn_player = Gtk.Button(label="Select Player Position")
        btn_player.connect("clicked", self.on_player_clicked)
        grid.attach(btn_player, 0, 1, 2, 1)

        btn_enemy = Gtk.Button(label="Select Enemy Position")
        btn_enemy.connect("clicked", self.on_enemy_clicked)
        grid.attach(btn_enemy, 0, 2, 2, 1)

        btn_calc = Gtk.Button(label="Prepare Normal Shot")
        btn_calc.connect("clicked", self.on_prepare_shot)
        grid.attach(btn_calc, 0, 3, 1, 1)

        btn_high = Gtk.Button(label="Prepare High Shot")
        btn_high.connect("clicked", self.on_prepare_high_shot)
        grid.attach(btn_high, 1, 3, 1, 1)

        self.status = Gtk.Label(label="Status: Waiting for input")
        grid.attach(self.status, 0, 4, 2, 1)

    def set_status(self, text):
        GLib.idle_add(self.status.set_text, f"Status: {text}")

    def get_wind(self):
        try:
            return int(self.wind_entry.get_text())
        except:
            return 0

    def on_player_clicked(self, widget):
        self.set_status("Click your tank")
        threading.Thread(target=self.select_player).start()

    def on_enemy_clicked(self, widget):
        self.set_status("Click enemy tank")
        threading.Thread(target=self.select_enemy).start()

    def on_prepare_shot(self, widget):
        if None not in (YourX, YourY, EnemyX, EnemyY):
            direction = "right" if YourX < EnemyX else "left"
            setTo100_90(YourX, YourY)
            setPowerAndAngle(round(velocity), angle, 100, 90, direction)
            self.set_status(f"Normal Shot: P={round(velocity)} A={angle}")

    def on_prepare_high_shot(self, widget):
        if None not in (YourX, YourY, EnemyX, EnemyY):
            direction = "right" if YourX < EnemyX else "left"
            setTo100_90(YourX, YourY)
            setPowerAndAngle(round(highVelocity), highAngle, 100, 90, direction)
            self.set_status(f"High Shot: P={round(highVelocity)} A={highAngle}")

    def select_player(self):
        with MouseListener(on_click=posPlayer) as listener:
            listener.join()
        self.set_status(f"Player Position: {YourX},{YourY}")
        self.try_calculate()

    def select_enemy(self):
        with MouseListener(on_click=posEnemy) as listener:
            listener.join()
        self.set_status(f"Enemy Position: {EnemyX},{EnemyY}")
        self.try_calculate()

    def try_calculate(self):
        if None not in (YourX, YourY, EnemyX, EnemyY):
            dx = abs(YourX - EnemyX)
            dy = YourY - EnemyY
            wind = self.get_wind()
            calcOptimal(dx, dy, wind)
            calcHighestBelow100(dx, dy, wind)
            self.set_status("Calculation complete")


if __name__ == "__main__":
    app = TankHelper()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
