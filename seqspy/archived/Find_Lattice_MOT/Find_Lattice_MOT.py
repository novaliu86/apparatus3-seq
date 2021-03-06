"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import sys
import os
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)


import time
t0=time.time()

import sys, math
 
 
 
import seq, wfm, gen, cnc, andor
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
exp      = float(report['FINDLATTICE']['andorexp'])
noatoms  = float(report['ANDOR']['noatoms'])


#Decides whether to shine on the probe beam or the MOT beams
##if gen.bstr('Fluor(T)/Abs(F)',report) == True:
##probe = 'motswitch'
##else:
##	probe = 'probe'
#At the moment we are just using the MOT beams for fluorescence imaging
probe = 'motswitch'

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

# Set powers for ir beams
ir_ss = 0.5
ir1  = wfm.wave('ir1pow', float(report['FINDLATTICE']['irpow1']), ir_ss)
ir2  = wfm.wave('ir2pow', float(report['FINDLATTICE']['irpow2']), ir_ss)
ir3  = wfm.wave('ir3pow', float(report['FINDLATTICE']['irpow3']), ir_ss)
odt0 = wfm.wave('odtpow', float(report['FINDLATTICE']['odtpow']), ir_ss)
ir1.appendhold(5*ir_ss)
ir2.appendhold(5*ir_ss)
ir3.appendhold(5*ir_ss)
odt0.appendhold(5*ir_ss)
s.analogwfm_add(ir_ss,[ir1,ir2,ir3,odt0])
s.wait(5*ir_ss)
s.wait(10.0)

#Edit cnc.py to change any of this
s, ENDCNC = cnc.run(s,'BASLER')

# Turn on IR beams
overlap = float(report['FINDLATTICE']['MOToverlap'])
s.wait(-overlap)
s.digichg('irttl1',1)
s.digichg('irttl2',1)
s.digichg('irttl3',1)
odt_on = float(report['FINDLATTICE']['odt'])
s.digichg('odtttl',odt_on)
s.wait(overlap)

#Take fluorescence imaging shot with the MOT beams. 
#LET MOT EXPAND
#s.wait(-1.0)
s.digichg('field',0)
#s.wait(1.0)
s.digichg('motswitch',0) 

tof = float(report['FINDLATTICE']['tof'])
s.wait(tof)

#TAKE PICTURES
#light = 'probe'
light = 'motswitch'
#light = 'bragg'
trap_on_picture = odt_on
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)
#print s.digital_chgs_str(500,100000.,['cameratrig','probe','odtttl','prshutter'])

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

import seqconf
s.save( seqconf.seqtxtout() )
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
