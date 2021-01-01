#!/usr/bin/env python

from datetime import datetime, timedelta
import json, math, urllib3
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

periods_per_hour = 2
duration = 6 # duration of process in periods, i.e. half-hours
max_range = 24 # how far to consider in periods, i.e. half-hours
value = 'value_inc_vat'
units = 'p'
date_format = '%Y-%m-%dT%H:%M:%SZ'
url = 'https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-J/standard-unit-rates/'
flip = True

time = datetime.now().replace(second=0, microsecond=0)
start = (time - timedelta(minutes = 30)).isoformat() + 'Z'
end = (time + timedelta(hours=(max_range/periods_per_hour+duration/periods_per_hour))).isoformat() + 'Z'

url = url + '?period_from='+start+'&period_to='+end
pm = urllib3.PoolManager()
response = pm.request('GET', url)
data = json.loads(response.data)['results']
data.reverse()
# print(data)
result = list(map(lambda x:x['value_exc_vat'],data))
maxi = max(result)
mini = min(result)

cheapest_index = 0
cheapest_result = 99999

num_periods = len(result) - duration
for i in range(0,num_periods):
    tot = 0
    for j in range(duration):
        tot+=result[i+j]
    tot /= duration
    if (tot < cheapest_result):
        cheapest_index = i
        cheapest_result = tot

goal_start = datetime.strptime(data[cheapest_index]['valid_from'],date_format)
diff = goal_start - time
hours = round(float(diff.seconds) / 1800)/2

print('cheapest in {} hours'.format(hours))
print('cheapest avg = {}p'.format(round(cheapest_result,2)))

maxwidth = 100
maxval = 25
minval = -5
interval = maxwidth / (maxi - mini)

for i in range(0,len(result)):
    val = int(round(result[i]))
    index = datetime.strptime(data[i]['valid_from'],date_format).strftime('%H:%M')
    active = '-'
    if ((i >= cheapest_index) & (i < cheapest_index + duration)):
        active = '+'
    if (val < 0):
        print('{} {}{}{}'.format(index,' '*(5 + val),'#'*(-1 * val),active))
    elif (val > 0):
        print('{} {}{}{}'.format(index,' '*5,active,'#'*val))
    else:
        print('{} {}{}'.format(index,' '*5,active))

### IMAGE ###

inkyphat = InkyPHAT('black')
width = inkyphat.WIDTH
height = inkyphat.HEIGHT
padding = 1
white = inkyphat.WHITE
black = inkyphat.BLACK
grey = (white + black)/2

img = Image.new('P',(width,height),black)
draw = ImageDraw.Draw(img)

### TEXT ###

font_big = ImageFont.truetype('./FredokaOne-Regular.ttf', 40)
font_med = ImageFont.truetype('./FredokaOne-Regular.ttf', 32)
font_sml = ImageFont.truetype('./ConnectionIII.otf', 10)

message1 = '{}h'.format(hours)
w, h = font_big.getsize(message1)
x = 0
y = 0
draw.text((padding, 4), message1, white, font_big)

hint1 = "delay"
draw.text((padding + (h/2), 0), hint1, white, font_sml)

message2 = '{}p'.format(round(cheapest_result,2))
w2, h2 = font_med.getsize(message2)
draw.text((width - padding - w2, 5), message2, white, font_med)

hint2 = "avg"
draw.text((width - padding - 10 - w2/2, 0), hint2, white, font_sml)

timer = time.strftime('%d/%m  %H:%M')
wt, ht = font_sml.getsize(timer)
draw.text((width - padding - wt,height - ht - padding), timer, white, font_sml)

### CHART ###
start_y = h + padding
end_y = height - padding
start_x = padding
end_x = width - padding

avail_width = end_x - start_x
avail_height = end_y - start_y

#diff = maxi - mini
diff = maxval - minval

y_step = avail_height / diff
zero_y = start_y + y_step * maxval

bar_width = float(avail_width) / len(result)
for i in range(0,len(result)):
    val = result[i]
    index = datetime.strptime(data[i]['valid_from'],date_format).strftime('%H:%M')
    fill = black
    if ((i >= cheapest_index) & (i < cheapest_index + duration)):
        fill = white
    if (val < 0):
        z=0#draw.rectangle([start_x + (i*bar_width), zero_y, (i*bar_width)+start_x+bar_width-1, zero_y - (y_step * val)], fill=fill, outline=grey)
    elif (val > 0):
        z=0#draw.rectangle([start_x + (i*bar_width), zero_y, (i*bar_width)+start_x+bar_width-1, zero_y - (y_step * val)], fill=fill, outline=grey)
    else:
        z=0#draw.rectangle([start_x + (i*bar_width), zero_y, (i*bar_width)+start_x+bar_width-1, zero_y], fill=fill, outline=grey)

#img.save("img.png")
if (flip):
    img = img.rotate(180)
inkyphat.set_image(img)
#inkyphat.show()

