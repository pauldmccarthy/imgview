#!/usr/bin/python
#
# loadimg.py - load an ANALYZE75 image into a 3D numpy array. Only
# 3D images, and a limited number of data types, are supported:
#
#   - DT_UNSIGNED_CHAR (2)  -> numpy.uint8
#   - DT_SIGNED_SHORT  (4)  -> numpy.short
#   - DT_SIGNED_INT    (8)  -> numpy.int32
#   - DT_FLOAT         (16) -> numpy.float32
#   - DT_DOUBLE        (32) -> numpy.double
#
# Author: Paul McCarthy <pauld.mccarthy@gmail.com>
#

import os
import sys
import numpy
import array
import struct

# Save headers/images as little or big endian by default?
_LITTLE_ENDIAN = True

def _need_byteswap(littleend):

  if littleend:
    if sys.byteorder == 'little': return False
    else:                         return True
  else:
    if sys.byteorder == 'little': return True
    else:                         return False
  
def _fmt(dt):

  if   dt == 2:  return 'B'
  elif dt == 4:  return 'h'
  elif dt == 8:  return 'i'
  elif dt == 16: return 'f'
  elif dt == 64: return 'd' 

  raise Error('Unsupported datatype: %u' % dt)

def _bitpix(dt):

  if   dt == 2:  return 8
  elif dt == 4:  return 16
  elif dt == 8:  return 32
  elif dt == 16: return 32
  elif dt == 64: return 64
    
  raise Error('Unsupported datatype: %u' % dt)

def loadhdr(hdrfile):
  '''
  Load an ANALYZE75 header file, returning
  the important information in a dict.
  '''

  hdr = {}

  with open(hdrfile, 'rb') as f:

    bytes = f.read(348)

    magic = struct.unpack('>I', bytes[0:4])[0]
    cigam = struct.unpack('<I', bytes[0:4])[0]

    if   magic == 348: order = '>'
    elif cigam == 348: order = '<'
    else:              raise Error('Not an ANALYZE75 header file')

    hdr['xn'] = struct.unpack('%sH' % order, bytes[42:44])[0]
    hdr['yn'] = struct.unpack('%sH' % order, bytes[44:46])[0]
    hdr['zn'] = struct.unpack('%sH' % order, bytes[46:48])[0]

    hdr['dt'] = struct.unpack('%sH' % order, bytes[70:72])[0]
    hdr['bp'] = struct.unpack('%sH' % order, bytes[72:74])[0]

    hdr['xl'] = struct.unpack('%sf' % order, bytes[80:84])[0]
    hdr['yl'] = struct.unpack('%sf' % order, bytes[84:88])[0]
    hdr['zl'] = struct.unpack('%sf' % order, bytes[88:92])[0]

    hdr['littleend'] = (order == '<')
    
  return hdr

def _loadimg(fname, hdr):
  '''
  Load the ANALYZE75 image file for the corresponding header.
  The image is returned as a 3D numpy array with an appropriate
  numpy datatype.
  '''

  xn     = hdr['xn']
  yn     = hdr['yn']
  zn     = hdr['zn']
  dt     = hdr['dt']
  little = hdr['littleend']

  needswap = _need_byteswap(little)

  valsz = hdr['bp'] / 8
  
  if   dt == 2:  img = numpy.zeros((xn, yn, zn), numpy.uint8)
  elif dt == 4:  img = numpy.zeros((xn, yn, zn), numpy.short)
  elif dt == 8:  img = numpy.zeros((xn, yn, zn), numpy.int32)
  elif dt == 16: img = numpy.zeros((xn, yn, zn), numpy.float32)
  elif dt == 64: img = numpy.zeros((xn, yn, zn), numpy.double)
  else:          raise Error('Unsupported datatype: %u' % dt)

  fmt = _fmt(dt)

  with open(fname, 'rb') as f:

    for zi in range(zn):
      for yi in range(yn):

        xdata = array.array(fmt)
        xdata.fromfile(f, xn)
        if needswap: xdata.byteswap()        
        img[:,yi,zi] = xdata

  return img


def loadimg(fname):
  '''
  Load an ANALYZE75 image and header; they are returned as a tuple.
  '''

  fpref = os.path.splitext(fname)[0]

  hdr =  loadhdr('%s.hdr' % fpref)
  img = _loadimg('%s.img' % fpref, hdr)
  
  return (img, hdr)


def saveimg(img, fname, xl, yl, zl, little=_LITTLE_ENDIAN):
  '''
  Save the given image. It is assumed that the
  image is in the appropriate numpy datatype.
  '''

  if   img.dtype == numpy.uint8:    dt = 2
  elif img.dtype == numpy.short:    dt = 4
  elif img.dtype == numpy.int32:    dt = 8
  elif img.dtype == numpy.float32:  dt = 16
  elif img.dtype == numpy.double:   dt = 64
  else: raise Error('Unsupported datatype: %s' % img.dtype)

  fmt = _fmt(dt)

  (xn,yn,zn) = img.shape

  fpref   = os.path.splitext(fname)[0]
  hdrname = '%s.hdr' % fpref
  needswap = _need_byteswap(little)

  _savehdr(hdrname, xn, yn, zn, xl, yl, zl, dt, little)

  with open(fname, 'wb') as f:

    for zi in range(zn):
      for yi in range(yn):

        data = array.array(fmt, img[:, yi, zi])
        if needswap: data.byteswap()
        data.tofile(f)


def _savehdr(fname, xn, yn, zn, xl, yl, zl, dt, little):
  '''
  Create an ANALYZE75 header file
  with the given information.
  '''

  if little: order = '<'
  else:      order = '>'

  headerbytes = ''

  headerbytes += struct.pack('%sI' % order, 348)
  headerbytes += '\00'*36
  headerbytes += struct.pack('%sH' % order, 4)
  headerbytes += struct.pack('%sH' % order, xn)
  headerbytes += struct.pack('%sH' % order, yn)
  headerbytes += struct.pack('%sH' % order, zn)
  headerbytes += struct.pack('%sH' % order, 1)
  headerbytes += struct.pack('%sH' % order, 1)
  headerbytes += struct.pack('%sH' % order, 1)
  headerbytes += struct.pack('%sH' % order, 1)
  headerbytes += '\00'*14
  headerbytes += struct.pack('%sH' % order, dt)
  headerbytes += struct.pack('%sH' % order, _bitpix(dt))

  headerbytes += '\00'*2
  headerbytes += struct.pack('%sf' % order, 0.0)
  headerbytes += struct.pack('%sf' % order, xl)
  headerbytes += struct.pack('%sf' % order, yl)
  headerbytes += struct.pack('%sf' % order, zl)
  headerbytes += '\00'*256

  with open(fname, 'wb') as f:
    f.write(headerbytes)


def imgvalue(img, hdr, x, y, z):
  '''
  Return the image value at the given real coordinates.
  '''

  xl = hdr['xl']
  yl = hdr['yl']
  zl = hdr['zl']

  xi = int(round(x/xl))
  yi = int(round(y/yl))
  zi = int(round(z/zl))
  
  return img[xi,yi,zi] 
