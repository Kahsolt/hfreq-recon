from torch.autograd import grad

from attacks.base import *

class MIFGSMAttack(BaseAttack):
    
  def __init__(self, model:Model, eps:float=0.03, alpha:float=0.01, steps:int=40, random_start:bool=True, dfn:Callable=None, decay:float=1.0):
    super().__init__(model, dfn)
    
    self.model = model
    self.dfn = dfn or (lambda _: _)
    self.eps = eps
    self.alpha = alpha
    self.steps = steps
    self.decay = decay
    self.random_start = random_start
        
  @torch.no_grad()
  def __call__(self, X:Tensor, Y:Tensor) -> Tensor:
    X = X.clone().detach()
    Y = Y.clone().detach()
    AX = X.clone().detach()
    momentum = torch.zeros_like(X).detach()
    
    if self.random_start:
      AX = AX + torch.empty_like(AX).uniform_(-self.eps, self.eps)
      AX = self.std_clip(AX).detach()
      
    for _ in tqdm(range(self.steps)):
      AX.requires_grad = True
      
      with torch.enable_grad():
        outputs = self.model_forward(AX)
        loss = torch.nn.CrossEntropyLoss()
        cost = loss(outputs, Y)
      
      g = grad(cost, AX, grad_outputs= cost, retain_graph=False, create_graph=False)[0]
      g = g / torch.mean(torch.abs(g), dim=(1, 2, 3), keepdim=True)
      g = g + momentum * self.decay
      momentum = g
      
      AX = AX.detach() + self.alpha * g.sign()
      delta = torch.clamp(AX - X, min=-self.eps, max=self.eps)
      AX = self.std_clip(X + delta).detach()
    
    return self.std_quant(AX)
  
if __name__ == '__main__':
  from plot import *
  # unitest
  pass