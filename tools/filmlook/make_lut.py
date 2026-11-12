import numpy as np, sys
from scipy.interpolate import PchipInterpolator
N=33
g=np.linspace(0,1,N)
# cube order: R fastest
B,G,R=np.meshgrid(g,g,g,indexing='ij')
rgb=np.stack([R,G,B],-1).reshape(-1,3)

def rgb2hsv(c):
    r,g,b=c[:,0],c[:,1],c[:,2]
    mx=c.max(1); mn=c.min(1); d=mx-mn
    h=np.zeros_like(mx)
    m=d>1e-6
    rm=m&(mx==r); gm=m&(mx==g)&~rm; bm=m&~rm&~gm
    h[rm]=((g-b)[rm]/d[rm])%6
    h[gm]=((b-r)[gm]/d[gm])+2
    h[bm]=((r-g)[bm]/d[bm])+4
    h=h*60
    s=np.where(mx>1e-6,d/np.maximum(mx,1e-6),0)
    return h,s,mx
def hsv2rgb(h,s,v):
    h=(h%360)/60; i=np.floor(h).astype(int)%6; f=h-np.floor(h)
    p=v*(1-s); q=v*(1-s*f); t=v*(1-s*(1-f))
    out=np.zeros((len(h),3))
    for k,(a,b,c) in enumerate([(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)]):
        m=i==k; out[m,0]=a[m]; out[m,1]=b[m]; out[m,2]=c[m]
    return out
def band(h,c,w):
    d=np.abs(((h-c)+180)%360-180)
    return np.clip(1-d/w,0,1)**1.5*1.0

h,s,v=rgb2hsv(rgb)
# hue shifts: foliage greens toward deep emerald, sky toward teal
h=h+ 10*band(h,105,45) - 8*band(h,215,35)
# saturation per hue
sat=0.90*np.ones_like(s)
sat*= 1-0.12*band(h,115,55)     # greens calmer
sat*= 1-0.12*band(h,210,40)     # skies calmer
sat*= 1+0.06*band(h,30,25)      # warm skin/wood/lanterns slightly richer
s=np.clip(s*sat,0,1)
out=hsv2rgb(h,s,v)

# filmic tone curve (lifted blacks, soft highlight roll-off)
xp=[0,0.10,0.25,0.5,0.75,0.92,1]
yp=[0.035,0.085,0.215,0.50,0.775,0.905,0.955]
curve=PchipInterpolator(xp,yp)
Y0=out@np.array([0.2126,0.7152,0.0722])
Y1=curve(np.clip(Y0,0,1))
ratio=np.where(Y0>1e-4,Y1/np.maximum(Y0,1e-4),1)
lum_mode=out*ratio[:,None]
chan_mode=curve(np.clip(out,0,1))
out=0.6*lum_mode+0.4*chan_mode

# split toning: shadows -> WayFare deep green/teal, highlights -> warm cream/gold
Y=out@np.array([0.2126,0.7152,0.0722])
ws=np.clip(1-Y/0.45,0,1)**1.6
wh=np.clip((Y-0.55)/0.45,0,1)**1.4
out+= ws[:,None]*np.array([-0.020,0.012,0.004])
out+= wh[:,None]*np.array([0.022,0.010,-0.028])
out=np.clip(out,0,1)
with open(sys.argv[1],'w') as f:
    f.write('TITLE "WayFare Film v1"\nLUT_3D_SIZE 33\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
    for r in out: f.write(f'{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\n')
print('ok')
