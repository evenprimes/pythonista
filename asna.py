'''asna.py -- yoga/excercise timer

A simple routine timer for yogis and such people that use a
series of timers. The layout works in both portrait and landscape
modes. I've tested the code on iPad and iPhone 8 Plus. The
layouts work for me on those devices, your milage may vary. ;)

The default included pose list is what i normally do. You can
also feed the list in on the command line (such as might happen
if you feed the contents of a text block or file from the iOS
Shortcuts app).

The format is:
  <item>,<duration in seconds>

The duration can be a float or int value.
Blank lines are ignored. Lines not in the correct format will
crash the script. No error correction was attempted.

There shouldn't be any *reasonable* limit to the number of
poses, but I only tested up to about 30.

License:
  I release this into the public domain. Be excellent to
  each other.
'''
import clipboard
import sound
import speech
import sys
import time
import ui

from objc_util import ObjCClass

POSELISTtest = """
Stretch left,10
Stretch right,5
"""

POSELIST = """
Left leg front,90
Right leg front,90
Split,90
Pike,90
Left leg front,90
Right leg front,90
Split,90
Pike,90
Kneel,60
Camel,90
Kneel,45
Camel,90
Kneel,30
Get on stomach,5
Boat,60
Rest,30
Boat,60
Rest,30
Sit up,5
Twist left,90
Twist right,90
Get on stomach,5
Plank,30
Rest,30
Plank,30
"""

ORANGE = '#dd5555'
DONE_COLOR = '#ffff00'
PROGRESS_COLOR = '#0000aa'
SHORTTIME_COLOR = '#aa2222'


class AsnaView(ui.View):
  def __init__(self, routine):
    '''build view tree and elements'''
    self.cancel_pressed = False
    self.pause_pressed = False
    self.background_color = 'black'
    self.name = 'asna'

    # This is the "parser" for the input list of poses. Don't
    # get sloppy with input and expect stuff to work.
    self.asnalist = [x.split(',') for x in routine.splitlines() if len(x) > 0]

    # Create the elements of the view. Layout done in .layout()
    # to support rotation.
    self.pose_name = ui.Label(text='pose name',
      text_color='white',
      alignment=ui.ALIGN_CENTER,
      font=('<system-bold>', 40),)
    self.add_subview(self.pose_name)

    self.pb_view = ui.View(background_color='#666666',
      corner_radius=10)
    self.pb = ui.View(background_color=DONE_COLOR)
    self.time_left = ui.Label(text='time left',
      text_color='white',
      font=('<system-bold>', 20),
      alignment=ui.ALIGN_CENTER)
    self.pb_view.add_subview(self.pb)
    self.pb_view.add_subview(self.time_left)
    self.add_subview(self.pb_view)

    self.pause_button = ui.Button(title='Pause',
      action=self.press_pause,
      font=('<system-bold>', 24),
      alignment=ui.ALIGN_CENTER)
    self.pause_button.width = 240
    self.add_subview(self.pause_button)

    self.begin_button = ui.Button(title='Begin',
      action=self.press_begin,
      font=('<system-bold>', 18))
    self.add_subview(self.begin_button)

    self.cancel_button = ui.Button(title='Cancel',
      action=self.press_cancel,
      font=('<system-bold>', 18))
    self.add_subview(self.cancel_button)

    self.reset()

  def layout(self):
    '''handle layout and rotation'''
    width, height = ui.get_screen_size()
    self.width = width
    self.height = height
    self.pose_name.frame = (20, height * 0.1, width - 40, 60)
    self.pb_view.frame = (20, height * 0.35, width - 40, 50)
    self.pb.frame = (0, 0, self.pb_view.width, self.pb_view.height)
    self.time_left.frame = (0, 0, self.pb_view.width, self.pb_view.height)
    self.pause_button.center = (width / 2, height * 0.55)
    self.begin_button.center = (width / 2, height * 0.8)
    self.cancel_button.center = (width / 2, height * 0.8)

  def reset(self):
    '''cleanup ui, prep for action'''
    self.pause_button.enabled = False
    self.pause_button.hidden = True

    self.cancel_button.enabled = False
    self.cancel_button.hidden = True

    self.begin_button.enabled = True
    self.begin_button.hidden = False

    self.pose_name.text = 'current pose'
    self.update_progress_bar(1.0, '', DONE_COLOR)

    # Enable screen sleeping.
    ObjCClass('UIApplication').sharedApplication().idleTimerDisabled = False

  def setup_begin(self):
    '''game on, prep cancel and pause buttons'''
    self.pause_button.enabled = True
    self.pause_button.hidden = False

    self.cancel_button.enabled = True
    self.cancel_button.hidden = False

    self.begin_button.enabled = False
    self.begin_button.hidden = True

    self.pb.width = 0
    self.cancel_pressed = False

    # Disable screen sleeping.
    ObjCClass('UIApplication').sharedApplication().idleTimerDisabled = True

  def update_progress_bar(self, percent_width, status, pbcolor):
    '''redraw the progress bar and update status text'''
    self.pb.width = self.pb_view.width * percent_width
    self.pb.background_color = pbcolor
    self.time_left.text = status

  @ui.in_background
  def press_begin(self, sender):
    self.setup_begin()

    for pose, hold_time in self.asnalist:
      if self.cancel_pressed:
        # Break out right away if we can.
        break

      hold_time = float(hold_time)
      pose_finished = False
      pause_time = None
      start_time = time.time()
      end_time = start_time + hold_time
      tone5 = True
      tone3 = True

      self.pose_name.text = pose
      speech.say(pose, 'en_US')
      while not pose_finished:
        current_time = time.time()
        if self.cancel_pressed:
          # We only break out of one loop at a time. Handle
          # this first.
          break
        if self.pause_pressed and pause_time is None:
          pause_time = current_time - start_time
        elif self.pause_pressed:
          pass
        elif not self.pause_pressed and pause_time is not None:
          start_time = current_time - pause_time
          end_time = start_time + hold_time
          pause_time = None
        else:
          time_left = end_time - current_time
          pose_finished = current_time >= end_time
          if hold_time > 20 and time_left < 3.5 and tone5:
            # This sucks, but I did not see a better way to sound
            # a tone, but only one time, than to flag when it was
            # done. The tones sound pleasant to my ear at these
            # times.
            tone5 = False
            sound.play_effect('digital:Tone1')
          if time_left < 1.5 and tone3:
            tone3 = False
            sound.play_effect('digital:TwoTone1')
          self.update_progress_bar((current_time-start_time)/hold_time,
            f"{round(time_left)}",   # ooh, fancy f-string!
            PROGRESS_COLOR if time_left > 4 else SHORTTIME_COLOR)
        time.sleep(0.01)
      sound.play_effect('drums:Drums_07')
    self.reset()

  def press_cancel(self, sender):
    self.cancel_pressed = True

  def press_pause(self, sender):
    '''if running, start pause, otherwise resume'''
    if self.pause_pressed:
      # now resume
      self.pause_button.title = 'Pause'
      self.pause_pressed = False
    else:
      # original pause press
      self.pause_button.title = 'Resume'
      self.pause_pressed = True


if __name__ == '__main__':
  av = AsnaView(POSELIST if len(sys.argv) == 1 else sys.argv[1])
  av.present('fullscreen')
