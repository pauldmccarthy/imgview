#!/usr/bin/python
#
# imgview.py - Interactive ANALYZE75 image file viewer.
#
# Wx code and matplotlib <-> wx integration code gratefully stolen from:
#
#   http://eli.thegreenplace.net/2008/08/01/matplotlib-with-wxpython-guis/
#
# Author: Paul McCarthy <pauld.mccarthy@gmail.com>
#

import os
import sys

import wx
import numpy
import matplotlib

import loadimg

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

class ImageFrame(wx.Frame):

  def __init__(self, fname, hdr, img):
    wx.Frame.__init__(self, None, -1, 'imgview: %s' % fname);

    self.hdr = hdr
    self.img = img

    self.create_img_panel()
    self.on_x_slider(None)
    self.on_y_slider(None)
    self.on_z_slider(None)

  def create_img_panel(self):

    self.panel = wx.Panel(self)

    self.dpi    = 100
    self.fig    = Figure()
    self.canvas = FigCanvas(self.panel, -1, self.fig)

    self.fig.subplots_adjust(
      hspace=0.01,wspace=0.01,left=0.01,right=0.99,top=0.99,bottom=0.01)    

    self.zax = self.fig.add_subplot(1,3,1)
    self.yax = self.fig.add_subplot(1,3,2)    
    self.xax = self.fig.add_subplot(1,3,3)

    self.zax_slider = wx.Slider(
      self.panel,
      value=self.hdr['zn'] / 2.0,
      minValue=0.0,
      maxValue=self.hdr['zn']-1,
      style=wx.SL_HORIZONTAL)

    self.yax_slider = wx.Slider(
      self.panel,
      value=self.hdr['yn'] / 2.0,
      minValue=0.0,
      maxValue=self.hdr['yn']-1,
      style=wx.SL_HORIZONTAL)

    self.xax_slider = wx.Slider(
      self.panel,
      value=self.hdr['xn'] / 2.0,
      minValue=0.0,
      maxValue=self.hdr['xn']-1,
      style=wx.SL_HORIZONTAL)

    self.Bind(wx.EVT_SLIDER, self.on_z_slider, self.zax_slider)
    self.Bind(wx.EVT_SLIDER, self.on_y_slider, self.yax_slider)    
    self.Bind(wx.EVT_SLIDER, self.on_x_slider, self.xax_slider)


    self.zax_text = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
    self.yax_text = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
    self.xax_text = wx.TextCtrl(self.panel, style=wx.TE_READONLY)

    self.slibox = wx.BoxSizer(wx.HORIZONTAL)
    self.slibox.Add(self.zax_slider, proportion=1)
    self.slibox.Add(self.yax_slider, proportion=1)
    self.slibox.Add(self.xax_slider, proportion=1)

    self.dimbox = wx.BoxSizer(wx.HORIZONTAL)
    self.dimbox.Add(self.zax_text, proportion=1)
    self.dimbox.Add(self.yax_text, proportion=1)
    self.dimbox.Add(self.xax_text, proportion=1)

    self.layoutbox = wx.BoxSizer(wx.VERTICAL)
    self.layoutbox.Add(self.canvas, proportion=9, flag=wx.EXPAND)
    self.layoutbox.Add(self.slibox, proportion=1, flag=wx.EXPAND)
    self.layoutbox.Add(self.dimbox, proportion=1, flag=wx.EXPAND)
    
    self.panel.SetSizer(self.layoutbox)
    self.layoutbox.Fit(self)


  def _draw_ax(self, ax, data, xlim,ylim):

    ax.clear()
    ax.pcolormesh(data,cmap='gray', vmin=self.img.min(), vmax=self.img.max())
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim((0,xlim-1))
    ax.set_ylim((0,ylim-1))
    self.canvas.draw()

  def on_x_slider(self, event):
    
    val = self.xax_slider.GetValue()
    self.xax_text.SetValue('%u' % val)
    data = self.img[val,:,:].transpose()
    self._draw_ax(self.xax, data, self.hdr['yn'], self.hdr['zn'])
    
  def on_y_slider(self, event):

    val = self.yax_slider.GetValue()
    self.yax_text.SetValue('%u' % val)
    data = self.img[:,val,:].transpose()
    self._draw_ax(self.yax, data, self.hdr['xn'], self.hdr['zn'])
    
  def on_z_slider(self, event):
    val = self.zax_slider.GetValue()
    self.zax_text.SetValue('%u' % val)
    data = self.img[:,:,val].transpose()
    self._draw_ax(self.zax, data, self.hdr['xn'], self.hdr['yn'])

if __name__ == '__main__':

  if len(sys.argv) != 2:
    print 'usage: imgview.py filename'
    exit()

  imgfile = sys.argv[1]

  (img,hdr) = loadimg.loadimg(imgfile)

  app = wx.PySimpleApp()
  app.frame = ImageFrame(imgfile, hdr, img)
  app.frame.Show()
  app.MainLoop()
