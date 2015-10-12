#!/usr/bin/python -OO
# -*- coding: utf-8 -*-

'''
This will execute when steelsquid-kiss-os starts.
Execute until system shutdown.
 - Mount and umount drives
 - Start web-server
 - Start event handler
 - 
@organization: Steelsquid
@author: Andreas Nilsson
@contact: steelsquid@gmail.com
@license: GNU Lesser General Public License v2.1
@change: 2013-10-25 Created
'''
import sys
import steelsquid_event
import steelsquid_utils
import steelsquid_i2c
import os
import time
import thread    
import getpass
from subprocess import Popen, PIPE, STDOUT
import subprocess
import os.path, pkgutil
import importlib
import expand
import signal
from io import TextIOWrapper, BytesIO


if steelsquid_utils.is_raspberry_pi:
    try:
        import steelsquid_pi
    except:
        steelsquid_utils.shout("Fatal error when import steelsquid_pi", is_error=True)


if steelsquid_utils.get_flag("piio"):
    try:
        import steelsquid_piio
    except:
        steelsquid_utils.shout("Fatal error when import steelsquid_piio", is_error=True)


def signal_term_handler(signal, frame):
    '''
    SIGTERM
    '''
    steelsquid_event.deactivate_event_handler()


# Listen for SIGTERM
signal.signal(signal.SIGTERM, signal_term_handler)


def print_help():
    '''
    Print help to the screen
    '''
    from steelsquid_utils import printb
    print("")
    printb("DESCRIPTION")
    print("Start and stop the Steelsquid daemon")
    print("")
    printb("steelsquid-boot start")
    print("Start the deamon")
    print("")
    printb("steelsquid-boot stop")
    print("Stop the daemon")
    print("\n")
    

def do_mount():
    '''
    Mount sshfs and samba
    '''
    mount_list = steelsquid_utils.get_list("sshfs")
    for row in mount_list:
        row = row.split("|")
        ip = row[0]
        port = row[1]
        user = row[2]
        password = row[3]
        local = row[4]
        remote = row[5]
        if len(password) > 0 and not steelsquid_utils.is_mounted(local):
            try:
                steelsquid_utils.mount_sshfs(ip, port, user, password, remote, local)
            except:
                steelsquid_utils.shout()
    mount_list = steelsquid_utils.get_list("samba")
    for row in mount_list:
        row = row.split("|")
        ip = row[0]
        user = row[1]
        password = row[2]
        local = row[3]
        remote = row[4]
        if not steelsquid_utils.is_mounted(local):
            try:
                steelsquid_utils.mount_samba(ip, user, password, remote, local)
            except:
                steelsquid_utils.shout()


def do_umount():
    '''
    Umount sshfs and samba
    '''
    mount_list = steelsquid_utils.get_list("sshfs")
    for row in mount_list:
        row = row.split("|")
        ip = row[0]
        local = row[4]
        remote = row[5]
        steelsquid_utils.umount(local, "ssh", ip, remote)
    mount_list = steelsquid_utils.get_list("samba")
    for row in mount_list:
        row = row.split("|")
        ip = row[0]
        local = row[3]
        remote = row[4]
        steelsquid_utils.umount(local, "samba", ip, remote)


def on_mount(args, para):
    '''
    On ssh, samba, usv or cd mount
    '''
    service = para[0]
    remote = para[1]
    local = para[2]
    steelsquid_utils.shout("MOUNT %s\n%s\nTO\n%s" %(service, remote, local))


def on_umount(args, para):
    '''
    On ssh, samba, usv or cd umount
    '''
    service = para[0]
    remote = para[1]
    local = para[2]
    steelsquid_utils.shout("UMOUNT %s\n%s\nFROM\n%s" %(service, remote, local))
                

def on_vpn(args, para):
    '''
    On vpn up/down
    '''
    stat = para[0]
    name = para[1]
    ip = para[2]
    shout_string = []
    if stat == "up":
        steelsquid_utils.shout("VPN ENABLED\n"+name + "\nIP\n" + ip)
    else:
        steelsquid_utils.shout("VPN DISABLED\n"+name)


def on_network(args, para):
    '''
    On network update
    '''
    net = para[0]
    wired = para[1]
    wifi = para[2]
    access_point = para[3]
    wan = para[4]
    bluetooth = ""
    if steelsquid_utils.get_flag("bluetooth_pairing") and steelsquid_utils.get_flag("piio"):
        answer = steelsquid_utils.execute_system_command(["hciconfig", "-a"])
        for line in answer:
            if "Name: " in line:
                line = line.replace("Name: '","")
                line = line.replace("'","")
                bluetooth = line
                break
        if bluetooth == "":
            bluetooth = "\nBT: No local device"
        else:
            bluetooth = "\nBT: " + bluetooth
    if net == "up":
        try:
            shout_string = []
            if steelsquid_utils.get_flag("piio"):
                import steelsquid_piio
                steelsquid_piio.led_net(True)
                if access_point != "---":
                    shout_string.append("STEELSQUID PIIO V")
                    shout_string.append(steelsquid_piio.version)
                    shout_string.append("\nAP: ")
                    shout_string.append(access_point)
                    shout_string.append("\nWIFI: ")
                    shout_string.append(wifi)
                    if wan != "---":
                        shout_string.append("\nWAN: ")
                        shout_string.append(wan)
                else:
                    shout_string.append("STEELSQUID PIIO V")
                    shout_string.append(steelsquid_piio.version)
                    shout_string.append("\nWIRED: ")
                    shout_string.append(wired)
                    if wan != "---":
                        shout_string.append("\nWAN: ")
                        shout_string.append(wan)
                shout_string.append(bluetooth)
                shout_string.append("\nVOLTAGE: ")
                shout_string.append(str(steelsquid_piio.voltage()))
            else:
                if access_point != "---":
                    shout_string.append("WIFI\n")
                    shout_string.append(access_point)
                    shout_string.append("\n")
                    shout_string.append(wifi)
                    if wan != "---":
                        shout_string.append("\nWAN IP\n")
                        shout_string.append(wan)
                else:
                    shout_string.append("WIRED\n")
                    shout_string.append(wired)
                    if wan != "---":
                        shout_string.append("\nWAN IP\n")
                        shout_string.append(wan)
            mes = "".join(shout_string)
            steelsquid_utils.shout(mes, leave_on_lcd = True)
        except:
            steelsquid_utils.shout()
        do_mount()
    else:
        if steelsquid_utils.get_flag("piio"):
            import steelsquid_piio
            steelsquid_piio.led_net(False)
            shout_string = []
            shout_string.append("STEELSQUID PIIO V")
            shout_string.append(steelsquid_piio.version)
            shout_string.append("\nNo network!")
            shout_string.append(bluetooth)
            shout_string.append("\nVOLTAGE: ")
            shout_string.append(str(steelsquid_piio.voltage()))
            steelsquid_utils.shout("".join(shout_string), leave_on_lcd = True)
        else:
            steelsquid_utils.shout("No network!", leave_on_lcd = True)
        do_umount()


def on_shutdown(args, para):
    '''
    Shutdown system
    '''
    steelsquid_utils.shout("Goodbye :-(")
    if steelsquid_utils.get_flag("socket_connection"):
        try:
            steelsquid_kiss_global.socket_connection.stop()
        except:
            pass
    if steelsquid_utils.get_flag("web"):
        try:
            steelsquid_kiss_global.http_server.stop_server()
        except:
            pass
    if steelsquid_utils.get_flag("piio"):
        import steelsquid_piio
        steelsquid_piio.led_net(False)
        steelsquid_piio.led_bt(False)
    steelsquid_utils.execute_system_command_blind(['killall', 'aria2c'])


def on_shout(args, para):
    '''
    Shout message
    '''
    steelsquid_utils.shout(" ".join(para))


def on_shutdown_button(gpio):
    '''
    Shutdown button pressed (GPIO)
    '''
    steelsquid_utils.execute_system_command_blind(['shutdown', '-h', 'now'], wait_for_finish=False)


def import_file_dyn(name):
    '''
    Load custom module
    '''
    try:
        importlib.import_module('expand.'+name)
    except:
        steelsquid_utils.shout("Fatal error when load custom module: " + 'expand.'+name, is_error=True)


def reload_file_dyn(name):
    '''
    Reload custom module
    '''
    try:
        steelsquid_utils.shout("Reload custom module: " + 'expand.'+name)
        the_lib = importlib.import_module('expand.'+name)
        reload(the_lib)
    except:
        steelsquid_utils.shout("Fatal error when reload custom module: " + 'expand.'+name, is_error=True)


def on_reload(args, para):
    '''
    Reload http/connection/custom modules
    '''
    if para[0] == "server":
        if steelsquid_utils.get_flag("web"):
            try:
                steelsquid_kiss_global.http_server.stop_server()
                steelsquid_utils.shout("Restart steelsquid_kiss_http_expand", debug=False)
                import steelsquid_kiss_http_server
                reload(steelsquid_kiss_http_server)
                reload(steelsquid_kiss_http_expand)
                steelsquid_kiss_global.http_server = steelsquid_kiss_http_expand.SteelsquidKissExpandHttpServer(None, steelsquid_utils.STEELSQUID_FOLDER+"/web/", steelsquid_utils.get_flag("web_authentication"), steelsquid_utils.get_flag("web_local"), steelsquid_utils.get_flag("web_authentication"), steelsquid_utils.get_flag("web_https"))
                steelsquid_kiss_global.http_server.start_server()
            except:
                steelsquid_utils.shout("Fatal error when restart steelsquid_kiss_http_expand", is_error=True)
        if steelsquid_utils.get_flag("socket_connection"):
            try:
                steelsquid_kiss_global.socket_connection.stop()
                steelsquid_utils.shout("Restart steelsquid_kiss_socket_expand", debug=False)
                import steelsquid_kiss_socket_connection
                reload(steelsquid_kiss_socket_connection)
                reload(steelsquid_kiss_socket_expand)
                steelsquid_kiss_global.socket_connection = steelsquid_kiss_socket_expand.SteelsquidKissSocketExpand(True)
                steelsquid_kiss_global.socket_connection.start()
            except:
                steelsquid_utils.shout("Fatal error when sestart steelsquid_kiss_socket_expand", is_error=True)
    elif para[0] == "custom":
        pkgpath = os.path.dirname(expand.__file__)
        for name in pkgutil.iter_modules([pkgpath]):
            thread.start_new_thread(reload_file_dyn, (name[1],))
    elif para[0] == "expand":
        thread.start_new_thread(import_expand, ()) 


class Logger(object):
    def write(self, message):
        '''
        Redirect sys.stdout to shout
        '''
        if message != None:
            if len(str(message).strip())>0:
                steelsquid_utils.shout(message, always_show=True)


def bluetooth_agent():
    '''
    Start the bluetooth_agent (enable pairing)
    '''
    while True:
        answer = steelsquid_utils.execute_system_command(["hciconfig", "-a"])
        bluetooth = None
        for line in answer:
            if "Name: " in line:
                line = line.replace("Name: '","")
                line = line.replace("'","")
                bluetooth = line
                break
        if bluetooth == None:
            steelsquid_utils.shout("No local bluetooth device found!")
        else:
            steelsquid_utils.shout("Start bluetooth: " + bluetooth)
            steelsquid_event.broadcast_event("network")
            if steelsquid_utils.get_flag("piio"):
                import steelsquid_piio
                steelsquid_piio.led_bt(True)
            try:
                proc=Popen("bluetoothctl", stdout=PIPE, stdin=PIPE, stderr=PIPE)
                proc.stdin.write('power on\n')
                proc.stdin.flush()
                time.sleep(1)
                proc.stdin.write('discoverable on\n')
                proc.stdin.flush()
                time.sleep(1)
                proc.stdin.write('pairable on\n')
                proc.stdin.flush()
                time.sleep(1)
                proc.stdin.write('agent on\n')
                proc.stdin.flush()
                time.sleep(1)
                proc.stdin.write('default-agent\n')
                proc.stdin.flush()
                while True:
                    proc_read = proc.stdout.readline()
                    if proc_read:
                        if "Request PIN code" in proc_read:
                            proc.stdin.write(steelsquid_utils.get_parameter("bluetooth_pin")+"\n")
                            proc.stdin.flush()
            except:
                steelsquid_utils.shout("Error on start bluetoothctl", is_error=True)
        if steelsquid_utils.get_flag("piio"):
            import steelsquid_piio
            steelsquid_piio.led_bt(False)
        time.sleep(20)    


def import_expand():
    '''
    Import the expand module
    '''
    try:
        if 'steelsquid_kiss_expand' in sys.modules:
            import steelsquid_kiss_expand
            reload(steelsquid_kiss_expand)
        else:
            import steelsquid_kiss_expand
    except:
        steelsquid_utils.shout("Fatal error when import steelsquid_kiss_expand", is_error=True)


def on_flag(args, para):
    '''
    Set/delete flag event
    '''
    if para[0]=="set":
        steelsquid_utils.set_flag(para[1])
    elif para[0]=="del":
        steelsquid_utils.del_flag(para[1])


def on_parameter(args, para):
    '''
    Set/delete parameter event
    '''
    if para[0]=="set":
        steelsquid_utils.set_parameter(para[1], " ".join(para[2:]))
    elif para[0]=="del":
        steelsquid_utils.del_parameter(para[1])


def on_pi_io_event(args, para):
    '''
    Execute io event from the command line
    '''
    if para[0] == "gpio_get":
        answer = steelsquid_pi.gpio_get(int(para[1]))
        steelsquid_utils.shout("gpio_get(" + para[1] + "): " + str(answer), always_show=True)
    elif para[0] == "gpio_set":
        steelsquid_pi.gpio_set(int(para[1]), steelsquid_utils.to_boolean(para[2]))
        steelsquid_utils.shout("gpio_set(" + para[1] + ", " + para[2] + "): OK", always_show=True)
    elif para[0] == "mcp23017_get":
        answer = steelsquid_pi.mcp23017_get(int(para[1]), int(para[2]))
        steelsquid_utils.shout("mcp23017_get(" + para[1] + ", " + para[2] + "): "+ str(answer), always_show=True)
    elif para[0] == "mcp23017_set":
        steelsquid_pi.mcp23017_set(int(para[1]), int(para[2]), steelsquid_utils.to_boolean(para[3]))
        steelsquid_utils.shout("mcp23017_set(" + para[1] + ", " + para[2] + ", " + para[3] + "): OK", always_show=True)
    elif para[0] == "ads1015":
        answer = steelsquid_pi.ads1015(para[1], int(para[2]))
        steelsquid_utils.shout("ads1015(" + para[1] + ", " + para[2] + "): "+ str(answer), always_show=True)
    elif para[0] == "mcp4725":
        steelsquid_pi.mcp4725(para[1], int(para[2]))
        steelsquid_utils.shout("mcp4725(" + para[1] + ", " + para[2] + "): OK", always_show=True)
    elif para[0] == "mcp4728":
        steelsquid_pi.mcp4728(para[1], para[2], para[3], para[4], para[5])
        steelsquid_utils.shout("mcp4728(" + para[1] + ", " + para[2] + ", " + para[3] + ", " + para[4] + ", " + para[5] + "): OK", always_show=True)
    elif para[0] == "hdd44780":
        if steelsquid_utils.to_boolean(para[1]):
            steelsquid_pi.hdd44780_write(para[2], number_of_seconds = 10, is_i2c=True)
        else:
            steelsquid_pi.hdd44780_write(para[2], number_of_seconds = 10, is_i2c=False)
        steelsquid_utils.shout("hdd44780_write(" + para[1] + ", " + para[2] + "): OK", always_show=True, to_lcd=False)
    elif para[0] == "nokia5110":
        steelsquid_pi.nokia5110_write(para[1], number_of_seconds = 10)
        steelsquid_utils.shout("nokia5110_write(" + para[1] + "): OK", always_show=True, to_lcd=False)
    elif para[0] == "ssd1306":
        steelsquid_pi.ssd1306_write(para[1], number_of_seconds = 10)
        steelsquid_utils.shout("ssd1306_write(" + para[1] + "): OK", always_show=True, to_lcd=False)
    elif para[0] == "hcsr04":
        answer = steelsquid_pi.hcsr04_distance(para[1], para[2])
        steelsquid_utils.shout("hcsr04_distance(" + para[1] + ", "+para[2]+ "): "+ str(answer), always_show=True)
    elif para[0] == "pca9685":
        steelsquid_pi.pca9685_move(para[1], para[2])
        steelsquid_utils.shout("hcsr04_distance(" + para[1] + ", "+para[2]+ "): OK", always_show=True)
    elif para[0] == "sabertooth":
        steelsquid_pi.sabertooth_motor_speed(para[2], para[3], para[1])
        steelsquid_utils.shout("sabertooth(" + para[1] + ", "+para[2]+ ", "+para[3]+ "): OK", always_show=True)
    elif para[0] == "trex_motor":
        steelsquid_pi.trex_motor(para[1], para[2])
        steelsquid_utils.shout("trex_motor(" + para[1] + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "trex_servo":
        steelsquid_pi.trex_servo(para[1], para[2])
        steelsquid_utils.shout("trex_servo(" + para[1] + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "trex_status":
        battery_voltage, left_motor_current, right_motor_current, accelerometer_x, accelerometer_y, accelerometer_z, impact_x, impact_y, impact_z = steelsquid_pi.trex_status()
        answer = []
        answer.append("battery_voltage: ")
        answer.append(str(battery_voltage))
        answer.append("\n")
        answer.append("left_motor_current: ")
        answer.append(str(left_motor_current))
        answer.append("\n")
        answer.append("right_motor_current: ")
        answer.append(str(right_motor_current))
        answer.append("\n")
        answer.append("accelerometer_x: ")
        answer.append(str(accelerometer_x))
        answer.append("\n")
        answer.append("accelerometer_y: ")
        answer.append(str(accelerometer_y))
        answer.append("\n")
        answer.append("accelerometer_z: ")
        answer.append(str(accelerometer_z))
        answer.append("\n")
        answer.append("impact_x: ")
        answer.append(str(impact_x))
        answer.append("\n")
        answer.append("impact_y: ")
        answer.append(str(impact_y))
        answer.append("\n")
        answer.append("impact_z: ")
        answer.append(str(impact_z))
        steelsquid_utils.shout("".join(answer), always_show=True)
    elif para[0] == "diablo":
        steelsquid_pi.diablo_motor_1(para[1])
        steelsquid_pi.diablo_motor_2(para[2])
        steelsquid_utils.shout("diablo(" + para[1] + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "servo12c":
        steelsquid_pi.servo12c(para[1], para[2])
        steelsquid_utils.shout("servo12c(" + para[1] + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "mpu6050_gyro":
        x, y, z = steelsquid_pi.mpu6050_gyro()
        steelsquid_utils.shout("mpu6050_gyro(): "+str(x)+", "+str(y)+", "+str(z), always_show=True)
    elif para[0] == "mpu6050_accel":
        x, y, z = steelsquid_pi.mpu6050_accel()
        steelsquid_utils.shout("mpu6050_accel(): "+str(x)+", "+str(y)+", "+str(z), always_show=True)
    elif para[0] == "mpu6050_rotation":
        x, y = steelsquid_pi.mpu6050_rotation()
        steelsquid_utils.shout("mpu6050_rotation(): "+str(x)+", "+str(y), always_show=True)
    elif para[0] == "po12_digital_out":
        steelsquid_pi.po12_digital_out(para[1], para[2])
        steelsquid_utils.shout("po12_digital_out(" + para[1] + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "po12_adc_pullup":
        steelsquid_pi.po12_adc_pullup(para[1])
        steelsquid_utils.shout("po12_adc_pullup(" + para[1]+ "): OK", always_show=True)
    elif para[0] == "po12_adc_vref":
        steelsquid_pi.po12_adc_vref(para[1])
        steelsquid_utils.shout("po12_adc_vref(" + para[1]+ "): OK", always_show=True)
    elif para[0] == "po12_adc":
        value = steelsquid_pi.po12_adc(para[1])
        steelsquid_utils.shout("po12_adc(" + para[1] + "): "+str(value), always_show=True)
    elif para[0] == "po12_adc_volt":
        value = steelsquid_pi.po12_adc_volt(para[1])
        steelsquid_utils.shout("po12_adc_volt(" + para[1] + "): "+str(value), always_show=True)
    elif para[0] == "po16_gpio_pullup":
        steelsquid_pi.po16_gpio_pullup(para[1], para[2])
        steelsquid_utils.shout("po16_gpio_pullup(" + para[1]  + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "po16_gpio_get":
        value = steelsquid_pi.po16_gpio_get(para[1])
        steelsquid_utils.shout("po16_gpio_get(" + para[1] + "): "+str(value), always_show=True)
    elif para[0] == "po16_gpio_set":
        steelsquid_pi.po16_gpio_set(para[1], para[2])
        steelsquid_utils.shout("po16_gpio_set(" + para[1]  + ", "+para[2] + "): OK", always_show=True)
    elif para[0] == "po16_pwm":
        steelsquid_pi.po16_pwm(para[1], para[2])
        steelsquid_utils.shout("po16_pwm(" + para[1]  + ", "+para[2] + "): OK", always_show=True)


def main():
    '''
    The main function
    '''    
    try:
        if len(sys.argv) < 2: 
            print_help()
        elif sys.argv[1] == "start":
            sys.stdout = Logger()
            if steelsquid_utils.get_flag("i2c_lock"):
                steelsquid_i2c.enable_locking(True)
            else:
                steelsquid_i2c.enable_locking(False)
            steelsquid_utils.execute_system_command_blind(["steelsquid", "keyboard", steelsquid_utils.get_parameter("keyboard")], wait_for_finish=False)
            steelsquid_utils.shout("Steelsquid Kiss OS "+steelsquid_utils.steelsquid_kiss_os_version()[1], False)
            if steelsquid_utils.get_flag("bluetooth_pairing"):
                steelsquid_utils.execute_system_command_blind(["hciconfig", "hci0", "piscan"], wait_for_finish=False)
                if not steelsquid_utils.has_parameter("bluetooth_pin"):
                    steelsquid_utils.set_parameter("bluetooth_pin", "1234")
                thread.start_new_thread(bluetooth_agent, ()) 
            if steelsquid_utils.is_raspberry_pi():
                if steelsquid_utils.get_flag("disable_monitor"):
                    steelsquid_utils.execute_system_command_blind(["/opt/vc/bin/tvservice", "-o"])
                if steelsquid_utils.get_flag("power"):
                    steelsquid_utils.shout("Listen for clean shutdown", debug=True)
                    steelsquid_pi.gpio_set(24, True)
                    steelsquid_pi.gpio_click(23, on_shutdown_button, steelsquid_pi.PULL_UP)
            if steelsquid_utils.get_flag("download"):
                if steelsquid_utils.get_parameter("download_dir") == "":
                    steelsquid_utils.set_parameter("download_dir", "/root")
                steelsquid_utils.execute_system_command_blind(['steelsquid', 'download-on'], wait_for_finish=False)
            steelsquid_utils.shout("Subscribe to events", debug=True)
            steelsquid_event.subscribe_to_event("shutdown", on_shutdown, ())
            steelsquid_event.subscribe_to_event("network", on_network, (), long_running=True)
            steelsquid_event.subscribe_to_event("vpn", on_vpn, ())
            steelsquid_event.subscribe_to_event("mount", on_mount, ())
            steelsquid_event.subscribe_to_event("umount", on_umount, ())
            steelsquid_event.subscribe_to_event("shout", on_shout, ())
            steelsquid_event.subscribe_to_event("reload", on_reload, ())
            steelsquid_event.subscribe_to_event("flag", on_flag, ())
            steelsquid_event.subscribe_to_event("parameter", on_parameter, ())
            steelsquid_event.subscribe_to_event("pi_io_event", on_pi_io_event, ())
            try:
                import steelsquid_kiss_global
            except:
                steelsquid_utils.shout("Fatal error when import steelsquid_kiss_global", is_error=True)
            try:
                import steelsquid_kiss_socket_expand
            except:
                steelsquid_utils.shout("Fatal error when import steelsquid_kiss_socket_expand", is_error=True)
            try:
                import steelsquid_kiss_http_expand
            except:
                steelsquid_utils.shout("Fatal error when import steelsquid_kiss_http_expand", is_error=True)
            if steelsquid_utils.get_flag("web"):
                try:
                    port = None
                    if steelsquid_utils.has_parameter("web_port"):
                        port = steelsquid_utils.get_parameter("web_port")
                    steelsquid_kiss_global.http_server = steelsquid_kiss_http_expand.SteelsquidKissHttpServerExpand(port, steelsquid_utils.STEELSQUID_FOLDER+"/web/", steelsquid_utils.get_flag("web_authentication"), steelsquid_utils.get_flag("web_local"), steelsquid_utils.get_flag("web_authentication"), steelsquid_utils.get_flag("web_https"))
                    steelsquid_kiss_global.http_server.start_server()
                except:
                    steelsquid_utils.shout("Fatal error when start steelsquid_kiss_http_expand", is_error=True)
            if steelsquid_utils.get_flag("socket_server"):
                try:
                    steelsquid_kiss_global.socket_connection = steelsquid_kiss_socket_expand.SteelsquidKissSocketExpand(True)
                    steelsquid_kiss_global.socket_connection.start()
                except:
                    steelsquid_utils.shout("Fatal error when start steelsquid_kiss_socket_expand as server", is_error=True)
            elif steelsquid_utils.has_parameter("socket_client"):
                try:
                    steelsquid_kiss_global.socket_connection = steelsquid_kiss_socket_expand.SteelsquidKissSocketExpand(False, steelsquid_utils.get_parameter("socket_client"))
                    steelsquid_kiss_global.socket_connection.start()
                except:
                    steelsquid_utils.shout("Fatal error when start steelsquid_kiss_socket_expand as server", is_error=True)            
            if steelsquid_utils.get_flag("piio"):
                steelsquid_kiss_global.PIIO.enable()
            if steelsquid_utils.get_flag("rover"):
                steelsquid_kiss_global.Rover.enable()
            if steelsquid_utils.get_flag("alarm"):
                steelsquid_kiss_global.Alarm.enable()                
            pkgpath = os.path.dirname(expand.__file__)
            for name in pkgutil.iter_modules([pkgpath]):
                steelsquid_utils.shout("Load custom module: " + 'expand.'+name[1], debug=True)                
                thread.start_new_thread(import_file_dyn, (name[1],)) 
            thread.start_new_thread(import_expand, ()) 
            steelsquid_utils.shout("Listen for events", debug=True)
            steelsquid_event.broadcast_event("network")
            steelsquid_event.activate_event_handler(create_ner_thread=False)
        elif sys.argv[1] == "stop":
            steelsquid_utils.shout("Goodbye :-(")
            steelsquid_utils.execute_system_command_blind(["event", "shutdown"])
    except:
        steelsquid_utils.shout("Fatal error when on boot steelsquid service", is_error=True)
        os._exit(0)


if __name__ == '__main__':
    main()

