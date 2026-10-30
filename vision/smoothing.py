class ExponentialSmoother:
    def __init__(self, alpha=0.35):
        self.alpha = alpha
        self.x = None
        self.y = None
        self.z = None

    def smooth(self, x, y, z):
        if self.x is None:
            self.x, self.y, self.z = x, y, z
        else:
            self.x = self.alpha * x + (1 - self.alpha) * self.x
            self.y = self.alpha * y + (1 - self.alpha) * self.y
            self.z = self.alpha * z + (1 - self.alpha) * self.z
        return self.x, self.y, self.z