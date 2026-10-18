# Decode panels 1 (kappa) and 2 (-psi) of l_io_slingshot_map.png through their own colourbars and test the relationship
# between them from the rendered pixels alone (no repository code). Colour limits are read from the bar geometry:
# kappa +-0.19, -psi +-42.4 (tick-spacing estimate, about +-1 %). Box coordinates are full-resolution pixels of the 2373x874 file.
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
im=np.array(Image.open('/home/rendier/Desktop/SpaceClaude/l_io_slingshot_map.png').convert('RGB')).astype(float); bg=im[5,5]
def lut(x,lim):
    col=im[:,x]; rows=[y for y in range(150,860) if np.abs(col[y]-bg).sum()>60]
    y0,y1=min(rows),max(rows); mid=(y0+y1)/2; half=(y1-y0)/2; ys=np.arange(y0,y1); return col[y0:y1],lim*(mid-ys)/half
c1,v1=lut(638,0.19); c2,v2=lut(1459,42.4)
def decode(box,cols,vals,thr=40):
    x0,x1,y0,y1=box; flat=im[y0:y1,x0:x1].reshape(-1,3); out=np.full(len(flat),np.nan)
    for i in range(0,len(flat),20000):
        d=((flat[i:i+20000,None,:]-cols[None,:,:])**2).sum(axis=2); j=d.argmin(axis=1); dm=d[np.arange(len(j)),j]
        v=vals[j].copy(); v[dm>thr**2]=np.nan; out[i:i+20000]=v   # labels/crosses are not on the colormap -> NaN
    return out.reshape(y1-y0,x1-x0)
K=decode((60,597,406,640),c1,v1); P=decode((881,1423,406,640),c2,v2)
fill=lambda a: np.where(np.isnan(a),np.nanmean(a),a)
Kf=fill(K); Pf=ndi.zoom(fill(P),(K.shape[0]/P.shape[0],K.shape[1]/P.shape[1]),order=1)
print('kappa range %+.3f..%+.3f ; -psi range %+.1f..%+.1f' % (np.nanmin(K),np.nanmax(K),np.nanmin(P),np.nanmax(P)))
print('Poisson check: if panel 2 = -psi with lap(psi)=2*kappa, then corr(kappa, laplacian(-psi)) must be negative')
for s in (3,6,10,16):
    Ks=ndi.gaussian_filter(Kf,s); Ps=ndi.gaussian_filter(Pf,s); L=ndi.laplace(Ps)
    print(f' sigma={s:2d}px  corr(kappa, lap(-psi)) = {np.corrcoef(Ks.ravel(),L.ravel())[0,1]:+.3f}   corr(kappa, -psi) = {np.corrcoef(Ks.ravel(),Ps.ravel())[0,1]:+.3f}')
for name,(mx,my) in {'lower blue lobe (112,22)':(112,22),'upper blue lobe (120,40)':(120,40)}.items():
    x=int(round((57+3.10*mx)-60)); y=int(round((642-3.06*my)-406))
    print(f' {name}: kappa {np.mean(Kf[y-3:y+3,x-3:x+3]):+.3f}   -psi {np.mean(Pf[y-3:y+3,x-3:x+3]):+.1f}   (mean of -psi {np.nanmean(P):+.1f})')
print(' variance share at scales >25 px: -psi %.0f %%, kappa %.0f %%' % (100*np.var(ndi.gaussian_filter(Pf,25))/np.var(Pf),100*np.var(ndi.gaussian_filter(Kf,25))/np.var(Kf)))
for t,l in ((-0.189,'darkest-blue end'),(0.19,'darkest-red end')):
    c=c1[np.abs(v1-t).argmin()]; print(f' share of panel-1 pixels at the {l}: {100*(np.abs(im[406:640,60:597]-c).sum(axis=2)<12).mean():.1f} %')
