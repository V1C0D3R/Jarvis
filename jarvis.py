from __future__ import print_function
from pync import Notifier
from phue import Bridge
from random import randint
from os import system

import myo as libmyo; libmyo.init('./myo.framework')
import time
import sys

class Jarvis():
    hue_bridge_ip = '192.168.0.29'
    default_bulb_id = 2
    request_interval = 0.1  # Output only 0.1 seconds
    default_voice_names = ["Zarvox", "Ava"]

    def __init__(self):
        print("Hi ! I'm Jarvis. Nice to meet you !")
        self.last_time = 0
        self.voiceNameId = 0
        self.initHueBridge()
        self.initMyo()
        
    def run(self):
        # Listen to keyboard interrupts and stop the hub in that case.
        try:
            while self.hub.running:
                time.sleep(0.25)
        except KeyboardInterrupt:
            print("\nQuitting ...")
        finally:
            print("Shutting down hub...")
            self.hub.shutdown()

    def initHueBridge(self):
        print("Connecting to bridge")
        try:
            self.hueBridge = HueControl(self, self.hue_bridge_ip)
        except Exception, e:
            print("Impossible to connect to bridge")
            raise e
            return
        print("Bridge connected.")


    def initMyo(self):
        print("Connecting to Myo ... Use CTRL^C to exit.")
        try:
            self.hub = libmyo.Hub()
        except MemoryError:
            print("Myo Hub could not be created. Make sure Myo Connect is running.")
            return
        print("Myo connected.")
        self.hub.set_locking_policy(libmyo.LockingPolicy.none)
        self.hub.run(1000, Listener(self))

    def say(self, text):
        Notifier.notify(text, title='Jarvis dit :')
        system('say -v "' + self.default_voice_names[self.voiceNameId] + '" "' + text + '"')

    def handleOrientation(self, orientation, pose):
        ctime = time.time()
        if (ctime - self.last_time) < self.request_interval:
            return
        self.last_time = ctime

        if orientation and pose == libmyo.Pose.fist:
            bri = int(round(((orientation.x+1.0)/2*154)+100, 0))
            sat = int(round(((orientation.y+1.0)/2*254), 0))
            hue = int(round(((orientation.w+1.0)/2*65280), 0))
            command = {'bri' : bri, 'sat' : sat, 'hue' : hue}
            self.hueBridge.setCommand(command)
            print("\r"+str(command), end=' ')
            sys.stdout.flush()

    def handleOnPose(self, myo, pose, lastPose):
        if pose == libmyo.Pose.double_tap:
            print("Double tap detected")
            myo.vibrate('short')
            myo.request_battery_level()
        elif pose == libmyo.Pose.fingers_spread:
            print("Fingers Spread detected")
            self.changeVoice("Good News")
            myo.vibrate('short')
            myo.vibrate('short')
        elif pose == libmyo.Pose.fist:
            myo.vibrate('short')
        elif pose == libmyo.Pose.rest and lastPose == libmyo.Pose.fist:
            myo.vibrate('short')

    def changeVoice(self, voiceName):
        try:
            voiceNameId = self.default_voice_names.index(voiceName)
            if self.voiceNameId == voiceNameId:
                message = "My voice remain the same"
            else:
                message = "This is my new voice"
        except ValueError, e:
            self.default_voice_names.append(voiceName)
            self.voiceNameId = self.default_voice_names.index(voiceName)
            message = "This is my new voice"
            print("This voice name does not exist in our default voice names list but we give a try")
        finally:
            self.say(message)



class HueControl():

    def initBridge(self, ip):
        self.bridge = Bridge(ip)
        self.bridge.connect()
        self.bridge.get_api()

    def __init__(self, jarvis, hueBridgeIP):
        self.initBridge(hueBridgeIP)
        self.jarvis = jarvis

    def setHue(self, hueValue):
        """
        Set Hue from 0 to 65280
        """
        
        self.bridge.set_light(2,'hue', hueValue)

    def setSaturation(self, satValue):
        """
        Set Saturation from 0 to 254
        """
        
        self.bridge.set_light(2,'sat', hueValue)

    def setBrightness(self, briValue):
        """
        Set brightness from 0 to 254
        """
        
        self.bridge.set_light(2,'bri', hueValue)

    def setCommand(self, command):
        
        self.bridge.set_light(2, command)

    def setState(self, state):
        
        self.bridge.set_light(2,'on', state)

    def getState(self):
        
        return self.bridge.get_light(2,'on')

    def toggleState(self):
        wantedState = not self.getState()
        self.setState(wantedState)


class Listener(libmyo.DeviceListener):
    """
    Listener implementation. Return False from any function to
    stop the Hub.
    """

    def __init__(self, jarvis):
        super(Listener, self).__init__()
        self.orientation = None
        self.pose = libmyo.Pose.rest
        self.emg_enabled = False
        self.locked = False
        self.rssi = None
        self.emg = None
        self.last_time = 0
        self.jarvis = jarvis

    def output(self):
        self.jarvis.handleOrientation(self.orientation, self.pose)

    def on_connect(self, myo, timestamp, firmware_version):
        myo.vibrate('short')
        myo.vibrate('short')
        myo.request_rssi()
        myo.request_battery_level()

    def on_rssi(self, myo, timestamp, rssi):
        self.rssi = rssi
        self.output()

    def on_pose(self, myo, timestamp, pose):
        self.jarvis.handleOnPose(myo, pose, self.pose)

        self.pose = pose
        self.output()

    def on_orientation_data(self, myo, timestamp, orientation):
        self.orientation = orientation
        self.output()

    def on_accelerometor_data(self, myo, timestamp, acceleration):
        pass

    def on_gyroscope_data(self, myo, timestamp, gyroscope):
        pass

    def on_emg_data(self, myo, timestamp, emg):
        self.emg = emg
        self.output()

    def on_unlock(self, myo, timestamp):
        self.locked = False
        self.output()

    def on_lock(self, myo, timestamp):
        self.locked = True
        self.output()

    def on_event(self, kind, event):
        """
        Called before any of the event callbacks.
        """

    def on_event_finished(self, kind, event):
        """
        Called after the respective event callbacks have been
        invoked. This method is *always* triggered, even if one of
        the callbacks requested the stop of the Hub.
        """

    def on_pair(self, myo, timestamp, firmware_version):
        """
        Called when a Myo armband is paired.
        """
        self.jarvis.say("Myo paired")

    def on_unpair(self, myo, timestamp):
        """
        Called when a Myo armband is unpaired.
        """
        self.jarvis.say("Myo unpaired")

    def on_disconnect(self, myo, timestamp):
        """
        Called when a Myo is disconnected.
        """

    def on_arm_sync(self, myo, timestamp, arm, x_direction, rotation,
                    warmup_state):
        """
        Called when a Myo armband and an arm is synced.
        """

    def on_arm_unsync(self, myo, timestamp):
        """
        Called when a Myo armband and an arm is unsynced.
        """

    def on_battery_level_received(self, myo, timestamp, level):
        """
        Called when the requested battery level received.
        """
        text = "Current Level is "+str(level)+"%"
        print(text, end='\n')
        self.jarvis.say(text)

    def on_warmup_completed(self, myo, timestamp, warmup_result):
        """
        Called when the warmup completed.
        """
        self.jarvis.say("Warmup completed")


def main():
    print("Initializing Jarvis...")
    try:
        jarvis = Jarvis()
    except Exception, e:
        raise e

    jarvis.run()

if __name__ == '__main__':
    main()

