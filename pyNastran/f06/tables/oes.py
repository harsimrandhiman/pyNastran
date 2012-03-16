from pyNastran.op2.tables.oes.oes_bars   import barStressObject
from pyNastran.op2.tables.oes.oes_solids import solidStressObject

class StressObject(object):
    def __init__(self,iSubcase,data):
        self.iSubcase = iSubcase
        self.grids = []
        #self.gridTypes = []
        #self.translations = []
        #self.rotations = []
        
        self.data = []
        self.addData(data)
        
    def addData(self,data):
        for line in data:
            self.data.append(line)
        return
            #(gridID,gridType,t1,t2,t3,t4,t5,t6) = line
            #self.grids.append(gridID)
            #self.gridTypes.append(gridType)
            #self.translations.append([t1,t2,t3])
            #self.rotations.append([t4,t5,t6])
        ###
        #print "grids = ",self.grids
    
    def __repr__(self):
        msg  = 'Composite Shell Element Stress\n'
        msg += "iSubcase = %s\n" %(self.iSubcase)
        for line in self.data:
            msg += '%s\n' %(line)
        return msg
            
        msg += '%-8s %8s %10s %10s %10s %10s %10s %10s\n' %('gridID','gridType','t1','t2','t3','t4','t5','t6')
        for (gridID,gridType,translation,rotation) in zip(self.grids,self.gridTypes,self.translations,self.rotations):
            (t1,t2,t3) = translation
            (t4,t5,t6) = rotation
            msg += "%-8i %8s %10.4g %10.4g %10.4g %10.4g %10.4g %10.4g\n" %(gridID,gridType,t1,t2,t3,t4,t5,t6)
        ###
        return msg

class IsoStressObject(object):
    def __init__(self,iSubcase,data,isFiberDistance,isVonMises):
        self.iSubcase = iSubcase
        self.grids = []
        self.isFiberDistance = isFiberDistance
        self.isVonMises = isVonMises

        self.data = []
        self.addData(data)
        
    def addData(self,data):        
        for line in data:
            self.data.append(line)
        return
    
    def __repr__(self):
        msg  = 'Isotropic Shell Element Stress\n'
        msg += "iSubcase = %s\n" %(self.iSubcase)
        for line in self.data:
            msg += '%s\n' %(line)
        return msg

class OES(object):
    def __init__(self):
        self.stress = {}
        self.isoStress = {}
        self.barStress = {}
        self.solidStress = {}

    def barStress(self):
        """
                                       S T R E S S E S   I N   B A R   E L E M E N T S          ( C B A R )
        ELEMENT        SA1            SA2            SA3            SA4           AXIAL          SA-MAX         SA-MIN     M.S.-T
          ID.          SB1            SB2            SB3            SB4           STRESS         SB-MAX         SB-MIN     M.S.-C
             12    0.0            0.0            0.0            0.0            1.020730E+04   1.020730E+04   1.020730E+04 
                   0.0            0.0            0.0            0.0                           1.020730E+04   1.020730E+04 
        analysisCode = 1 (Statics)
        deviceCode   = 1 (Print)
        tableCode    = 5 (Stress)
        sortCode     = 0 (Sort2,Real,Sorted Results) => sortBits = [0,0,0]
        formatCode   = 1 (Real)
        sCode        = 0 (Stress)
        numWide      = 8 (???)
        """
        (subcaseName,iSubcase,transient,analysisCode) = self.readSubcaseNameID()
        headers = self.skip(2)
        #print "headers = %s" %(headers)
        
        #isFiberDistance = False
        #isVonMises = False  # Von Mises/Max Shear
        #if 'DISTANCE' in headers:
        #    isFiberDistance = True
        #if 'VON MISES' in headers:
        #    isVonMises = True

        stressBits = self.makeStressBits()
        dataCode = {'log':self.log,'analysisCode':1,'deviceCode':1,'tableCode':5,'sortCode':0,
                    'sortBits':[0,0,0],'numWide':8,'sCode':0,'stressBits':stressBits,
                    'formatCode':1,'elementName':'CBAR','elementType':34,
                    }

        data = self.readBarStress()
        if iSubcase in self.barStress:
            self.barStress[iSubcase].addF06Data(data,transient)
        else:
            self.barStress[iSubcase] = barStressObject(dataCode,iSubcase,transient)
            self.barStress[iSubcase].addF06Data(data,transient)
        self.iSubcases.append(iSubcase)
    
    def readBarStress(self):
        """
        ELEMENT        SA1            SA2            SA3            SA4           AXIAL          SA-MAX         SA-MIN     M.S.-T
          ID.          SB1            SB2            SB3            SB4           STRESS         SB-MAX         SB-MIN     M.S.-C
             12    0.0            0.0            0.0            0.0            1.020730E+04   1.020730E+04   1.020730E+04 
                   0.0            0.0            0.0            0.0                           1.020730E+04   1.020730E+04 
        """
        data = []
        while 1:
            line = self.infile.readline()[1:].rstrip('\r\n ')
            sline = [line[0:12],line[12:27],line[27:42],line[42:57],line[57:64],line[64:86],line[86:101],line[101:116],line[116:131]]
            if 'PAGE' in line:
                break
            #print sline
            out = self.parseLineBlanks(sline,[int,float,float,float,float, float, float,float,float]) # line 1
            out = ['CBAR']+out
            #data.append(sline)
            line = self.infile.readline()[1:].rstrip('\r\n ')
            sline = [line[12:27],line[27:42],line[42:57],line[57:64],line[86:101],line[101:116],line[116:131]]
            #print sline
            out += self.parseLineBlanks(sline,[    float,float,float,float,        float,float,float]) # line 2
            #print "*",out
            data.append(out)
            self.i+=2
            ###
        ###
        #print "--------"
        #for line in data:
        #    print line
        #sys.exit()
        return data

    def quadCompositeStress(self):
        """
                       S T R E S S E S   I N   L A Y E R E D   C O M P O S I T E   E L E M E N T S   ( Q U A D 4 )
        ELEMENT  PLY  STRESSES IN FIBER AND MATRIX DIRECTIONS    INTER-LAMINAR  STRESSES  PRINCIPAL STRESSES (ZERO SHEAR)      MAX
          ID      ID    NORMAL-1     NORMAL-2     SHEAR-12     SHEAR XZ-MAT  SHEAR YZ-MAT  ANGLE    MAJOR        MINOR        SHEAR
            181    1   3.18013E+04  5.33449E+05  1.01480E+03   -7.06668E+01  1.90232E+04   89.88  5.33451E+05  3.17993E+04  2.50826E+05
            181    2   1.41820E+05  1.40805E+05  1.25412E+05   -1.06000E+02  2.85348E+04   44.88  2.66726E+05  1.58996E+04  1.25413E+05
        """
        (subcaseName,iSubcase,transient,analysisCode) = self.readSubcaseNameID()
        headers = self.skip(2)
        #print "headers = %s" %(headers)
        data = self.readTable([int,int,float,float,float,float,float,float,float,float,float])
        if iSubcase in self.stress:
            self.stress[iSubcase].addData(data)
        else:
            self.stress[iSubcase] = StressObject(iSubcase,data)
        self.iSubcases.append(iSubcase)
        #print self.stress[iSubcase]
        
    def triStress(self):
        """
                                 S T R E S S E S   I N   T R I A N G U L A R   E L E M E N T S   ( T R I A 3 )
        ELEMENT      FIBER               STRESSES IN ELEMENT COORD SYSTEM             PRINCIPAL STRESSES (ZERO SHEAR)                 
          ID.       DISTANCE           NORMAL-X       NORMAL-Y      SHEAR-XY       ANGLE         MAJOR           MINOR        VON MISES
              8   -1.250000E-01     -1.303003E+02   1.042750E+04  -1.456123E+02   -89.2100    1.042951E+04   -1.323082E+02   1.049629E+04
                   1.250000E-01     -5.049646E+02   1.005266E+04  -2.132942E+02   -88.8431    1.005697E+04   -5.092719E+02   1.032103E+04
        """
        (subcaseName,iSubcase,transient,analysisCode) = self.readSubcaseNameID()
        headers = self.skip(2)
        #print "headers = %s" %(headers)
        
        isFiberDistance = False
        isVonMises = False  # Von Mises/Max Shear
        if 'DISTANCE' in headers:
            isFiberDistance = True
        if 'VON MISES' in headers:
            isVonMises = True

        data = self.readTriStress()
        if iSubcase in self.isoStress:
            self.isoStress[iSubcase].addData(data)
        else:
            self.isoStress[iSubcase] = IsoStressObject(iSubcase,data,isFiberDistance,isVonMises)
        self.iSubcases.append(iSubcase)

    def readTriStress(self):
        """
                ELEMENT      FIBER               STRESSES IN ELEMENT COORD SYSTEM             PRINCIPAL STRESSES (ZERO SHEAR)                 
                  ID.       DISTANCE           NORMAL-X       NORMAL-Y      SHEAR-XY       ANGLE         MAJOR           MINOR        VON MISES
                      8   -1.250000E-01     -1.303003E+02   1.042750E+04  -1.456123E+02   -89.2100    1.042951E+04   -1.323082E+02   1.049629E+04
                           1.250000E-01     -5.049646E+02   1.005266E+04  -2.132942E+02   -88.8431    1.005697E+04   -5.092719E+02   1.032103E+04
        """
        data = []
        while 1:
            line = self.infile.readline()[1:].strip().split()
            if 'PAGE' in line:
                break
            print line
            sline = self.parseLine(line,[int,float, float,float,float, float,float,float, float]) # line 1
            sline = ['CTRIA3']+sline
            data.append(sline)
            line = self.infile.readline()[1:].strip().split()
            sline = self.parseLine(line,[    float, float,float,float, float,float,float, float]) # line 2
            data.append(sline)
            self.i+=2
            ###
        ###
        return data

    def quadStress(self):
        """
                             S T R E S S E S   I N   Q U A D R I L A T E R A L   E L E M E N T S   ( Q U A D 4 )        OPTION = BILIN

        ELEMENT              FIBER            STRESSES IN ELEMENT COORD SYSTEM         PRINCIPAL STRESSES (ZERO SHEAR)
          ID      GRID-ID   DISTANCE        NORMAL-X      NORMAL-Y      SHEAR-XY      ANGLE        MAJOR         MINOR       VON MISES
              6    CEN/4  -1.250000E-01  -4.278394E+02  8.021165E+03 -1.550089E+02   -88.9493   8.024007E+03 -4.306823E+02  8.247786E+03
                           1.250000E-01   5.406062E+02  1.201854E+04 -4.174177E+01   -89.7916   1.201869E+04  5.404544E+02  1.175778E+04

                       4  -1.250000E-01  -8.871141E+02  7.576036E+03 -1.550089E+02   -88.9511   7.578874E+03 -8.899523E+02  8.060780E+03
                           1.250000E-01  -8.924081E+01  1.187899E+04 -4.174177E+01   -89.8002   1.187913E+04 -8.938638E+01  1.192408E+04
        """
        (subcaseName,iSubcase,transient,analysisCode) = self.readSubcaseNameID()
        headers = self.skip(3)
        #print "headers = %s" %(headers)
        
        isFiberDistance = False
        isVonMises = False  # Von Mises/Max Shear
        if 'DISTANCE' in headers:
            isFiberDistance = True
        if 'VON MISES' in headers:
            isVonMises = True

        data = self.readQuadBilinear()
        if iSubcase in self.isoStress:
            self.isoStress[iSubcase].addData(data)
        else:
            self.isoStress[iSubcase] = IsoStressObject(iSubcase,data,isFiberDistance,isVonMises)
        self.iSubcases.append(iSubcase)

    def readQuadBilinear(self):
        data = []
        while 1:
            if 1: # CEN/4
                line = self.infile.readline()[1:].strip().split()
                if 'PAGE' in line:
                    return data
                sline = self.parseLine(line,[int,str,float, float,float,float, float,float,float, float]) # line 1
                sline = ['CQUAD4']+sline
                data.append(sline)
                line = self.infile.readline()[1:].strip().split()
                sline = self.parseLine(line,[        float, float,float,float, float,float,float, float]) # line 2
                data.append(sline)
                line = self.infile.readline() # blank line
                self.i+=3
            ###
            for i in range(4):
                line = self.infile.readline()[1:].strip().split()
                sline = self.parseLine(line,[int,float, float,float,float, float,float,float, float]) # line 1
                data.append(sline)
                line = self.infile.readline()[1:].strip().split()
                sline = self.parseLine(line,[    float, float,float,float, float,float,float, float]) # line 2
                data.append(sline)
                line = self.infile.readline() # blank line
                self.i+=3
            ###
        ###
        return data

    def solidStressHexa(self):
        return self.readSolidStress('CHEXA',8)
    def solidStressPenta(self):
        return self.readSolidStress('CPENTA',6)
    def solidStressTetra(self):
        return self.readSolidStress('CTETRA',4)

    def readSolidStress(self,eType,n):
        """
        analysisCode = 1 (Statics)
        deviceCode   = 1 (Print)
        tableCode    = 5 (Stress/Strain)
        sortCode     = 0 (Sort2,Real,Sorted Results) => sortBits = [0,0,0]
        formatCode   = 1 (Real)
        sCode        = 0 (Stress)
        numWide      = 8 (???)
        """
        (subcaseName,iSubcase,transient,analysisCode) = self.readSubcaseNameID()
        headers = self.skip(2)
        #print "headers = %s" %(headers)

        isMaxShear = True
        if 'VON MISES' in headers:
            isMaxShear = False
            
        data = self.read3DStress(eType,n)
        stressBits = self.makeStressBits(isMaxShear=False)
        dataCode = {'log':self.log,'analysisCode':1,'deviceCode':1,'tableCode':5,
                    'sortCode':0,'sortBits':[0,0,0],'numWide':8,'elementName':eType,'formatCode':1,
                    'sCode':0,'stressBits':stressBits}

        if iSubcase in self.solidStress:
            self.solidStress[iSubcase].addF06Data(data,transient)
        else:
            #self.solidStress[iSubcase] = SolidStressObject(iSubcase,data)
            self.solidStress[iSubcase] = solidStressObject(dataCode,iSubcase,transient)
            self.solidStress[iSubcase].addF06Data(data,transient)
        self.iSubcases.append(iSubcase)

    def makeStressBits(self,isMaxShear=True,isFiberDistance=True):
        stressBits = [0,0,0]
        if isMaxShear==False:
            stressBits[0] = 1
        
        if isFiberDistance:
            stressBits[2] = 1
        return stressBits
        
    def read3DStress(self,eType,n):
        data = []
        while 1:
            line = self.infile.readline().rstrip('\n\r') #[1:]
                    #              CENTER         X          #          XY             #        A         #
            sline = [line[1:17],line[17:24],line[24:28],line[28:43],line[43:47],line[47:63],line[63:66],line[66:80],  line[80:83],line[83:88],line[88:93],line[93:98],line[99:113],line[113:130]]
            sline = [s.strip() for s in sline]
            if 'PAGE' in line:
                break
            elif '' is not sline[0]:
                sline = [eType]+sline
            data.append(sline)
        ###
        return data
        