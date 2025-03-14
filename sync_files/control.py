#!/usr/bin/python3
import os, sys
sys.path.append("/usr/lib")
import kipr as k

def line_sense():
   thresh = 250
   max_strength = 50
   min_strength = 10

   val_l = k.analog(0)
   val_r = k.analog(1)

   if val_l > thresh:
      k.motor(3, int(min_strength + (max_strength - min_strength) * ((val_l - thresh) / 4096)))
   else:
      k.motor(3, 0)
   if val_r > thresh:
      k.motor(2, int(min_strength + (max_strength - min_strength) * ((val_l - thresh) / 4096)))
   else:
      k.motor(2, 0)

   return val_l, val_r

def main():
   while True: 
      line_sense()

if __name__ == "__main__":
   main()