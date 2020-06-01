import math

class DimOrder(object):
	"""
	Represents the order of the dimensions in a dataset's shape.
	"""
	ChannelHeightWidth = ['c', 'h', 'w']
	HeightWidthChannel = ['h', 'w', 'c']


class IterOrder(object):
	"""
	Represents the order of iterating over the dataset's dimensions.
	Dimensions are listed from the innermost, i.e. the one changing fastest, to the outermost.
	"""
	TransformHeightWidth = ['t', 'y', 'x']
	TransformWidthHeight = ['t', 'x', 'y']


class SlidingWindow(object):
	"""
	Represents a single window into a larger dataset.
	"""
	
	def __init__(self, x, y, w, h, dimOrder, transform = None):
		"""
		Creates a new window with the specified dimensions and transform
		"""
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.dimOrder = dimOrder
		self.transform = transform
	
	def apply(self, matrix):
		"""
		Slices the supplied matrix and applies any transform bound to this window
		"""
		view = matrix[ self.indices() ]
		return self.transform(view) if self.transform != None else view
	
	def getRect(self):
		"""
		Returns the window bounds as a tuple of (x,y,w,h)
		"""
		return (self.x, self.y, self.w, self.h)
	
	def setRect(self, rect):
		"""
		Sets the window bounds from a tuple of (x,y,w,h)
		"""
		self.x, self.y, self.w, self.h = rect
	
	def indices(self, includeChannel=True):
		"""
		Retrieves the indices for this window as a tuple of slices
		"""
		if self.dimOrder == DimOrder.HeightWidthChannel:
			
			# Equivalent to [self.y:self.y+self.h+1, self.x:self.x+self.w+1]
			return (
				slice(self.y, self.y+self.h),
				slice(self.x, self.x+self.w)
			)
			
		elif self.dimOrder == DimOrder.ChannelHeightWidth:
			
			if includeChannel is True:
				
				# Equivalent to [:, self.y:self.y+self.h+1, self.x:self.x+self.w+1]
				return (
					slice(None, None),
					slice(self.y, self.y+self.h),
					slice(self.x, self.x+self.w)
				)
				
			else:
				
				# Equivalent to [self.y:self.y+self.h+1, self.x:self.x+self.w+1]
				return (
					slice(self.y, self.y+self.h),
					slice(self.x, self.x+self.w)
				)
			
		else:
			raise Error('Unsupported order of dimensions: ' + str(self.dimOrder))
		
	def __str__(self):
		return '(' + str(self.x) + ',' + str(self.y) + ',' + str(self.w) + ',' + str(self.h) + ')'
	
	def __repr__(self):
		return self.__str__()


def generate(data, dimOrder, maxWindowSize, overlapPercent, transforms=[], overrideWidth=None, overrideHeight=None, iterorder=IterOrder.TransformHeightWidth):
	"""
	Generates a set of sliding windows for the specified dataset.
	"""
	
	# Determine the dimensions of the input data
	width = data.shape[dimOrder.index('w')]
	height = data.shape[dimOrder.index('h')]
	
	# Generate the windows
	return generateForSize(width, height, dimOrder, maxWindowSize, overlapPercent, transforms, overrideWidth, overrideHeight, iterorder)


def iterate_dims(xVals, yVals, tVals, iterorder):
	if iterorder == IterOrder.TransformHeightWidth:
		for x in xVals:
			for y in yVals:
				for t in tVals:
					yield x, y, t
	elif iterorder == IterOrder.TransformWidthHeight:
		for y in yVals:
			for x in xVals:
				for t in tVals:
					yield x, y, t
	else:
		raise Error('Unsupported iteration order: ' + str(iterorder))


def generateForSize(width, height, dimOrder, maxWindowSize, overlapPercent, transforms=[], overrideWidth=None, overrideHeight=None, iterorder=IterOrder.TransformWidthHeight):
	"""
	Generates a set of sliding windows for a dataset with the specified dimensions and order.
	"""
	
	# Create square windows unless an explicit width or height has been specified
	windowSizeX = maxWindowSize if overrideWidth is None else overrideWidth
	windowSizeY = maxWindowSize if overrideHeight is None else overrideHeight
	
	# If the input data is smaller than the specified window size,
	# clip the window size to the input size on both dimensions
	windowSizeX = min(windowSizeX, width)
	windowSizeY = min(windowSizeY, height)
	
	# Compute the window overlap and step size
	windowOverlapX = int(math.floor(windowSizeX * overlapPercent))
	windowOverlapY = int(math.floor(windowSizeY * overlapPercent))
	stepSizeX = windowSizeX - windowOverlapX
	stepSizeY = windowSizeY - windowOverlapY
	
	# Determine how many windows we will need in order to cover the input data
	lastX = width - windowSizeX
	lastY = height - windowSizeY
	xOffsets = list(range(0, lastX+1, stepSizeX))
	yOffsets = list(range(0, lastY+1, stepSizeY))
	
	# Unless the input data dimensions are exact multiples of the step size,
	# we will need one additional row and column of windows to get 100% coverage
	if len(xOffsets) == 0 or xOffsets[-1] != lastX:
		xOffsets.append(lastX)
	if len(yOffsets) == 0 or yOffsets[-1] != lastY:
		yOffsets.append(lastY)
	
	# Generate the list of windows
	windows = []
	for xOffset, yOffset, transform in iterate_dims(xOffsets, yOffsets, [None] + transforms, iterorder):
		windows.append(SlidingWindow(
			x=xOffset,
			y=yOffset,
			w=windowSizeX,
			h=windowSizeY,
			dimOrder=dimOrder,
			transform=transform
		))
	
	return windows


def generateRectanglarWindows(data, dimOrder, windowShape, overlapPercent, transforms=[], iterorder=IterOrder.TransformWidthHeight):
	"""
	Generates a set of sliding windows for the specified dataset, creating rectangular windows instead of square windows.
	`windowShape` must be a tuple specifying the desired window dimensions in (height,width) form.
	"""
	
	# Determine the dimensions of the input data
	width = data.shape[dimOrder.index('w')]
	height = data.shape[dimOrder.index('h')]
	
	# Generate the windows
	windowHeight, windowWidth = windowShape
	return generateForSize(
		width,
		height,
		dimOrder,
		0,
		overlapPercent,
		transforms,
		overrideWidth = windowWidth,
		overrideHeight = windowHeight,
		iterorder=iterorder,
	)


def generateForNumberOfWindows(data, dimOrder, windowCount, overlapPercent, transforms=[], iterorder=IterOrder.TransformWidthHeight):
	"""
	Generates a set of sliding windows for the specified dataset, automatically determining the required window size in
	order to create the specified number of windows. `windowCount` must be a tuple specifying the desired number of windows
	along the Y and X axes, in the form (countY, countX).
	"""
	
	# Determine the dimensions of the input data
	width = data.shape[dimOrder.index('w')]
	height = data.shape[dimOrder.index('h')]
	
	# Determine the window size required to most closely match the desired window count along both axes
	countY, countX = windowCount
	windowSizeX = math.ceil(width / countX)
	windowSizeY = math.ceil(height / countY)
	
	# Generate the windows
	return generateForSize(
		width,
		height,
		dimOrder,
		0,
		overlapPercent,
		transforms,
		overrideWidth = windowSizeX,
		overrideHeight = windowSizeY,
		iterorder=iterorder,
	)
