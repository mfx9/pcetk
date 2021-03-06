# Example script
from pCore                   import logFile
from pBabel                  import CHARMMParameterFiles_ToParameters, CHARMMPSFFile_ToSystem, CHARMMCRDFile_ToCoordinates3
from ContinuumElectrostatics import MEADModel, MEADSubstate, StateVector, TitrationCurves, MCModelDefault, MCModelGMCT


parameters = ["toppar/par_all27_prot_na.inp", ]

mol = CHARMMPSFFile_ToSystem ("lysozyme1990_xplor.psf", isXPLOR=True, parameters=CHARMMParameterFiles_ToParameters (parameters))
mol.coordinates3 = CHARMMCRDFile_ToCoordinates3 ("lysozyme1990.crd")


electrostaticModel = MEADModel (system=mol, pathMEAD="/home/mikolaj/local/bin/", pathScratch="mead", nthreads=1)

# Exclude cysteines involved in disulfide bonds.
# Also exclude all arginines, otherwise the system has too many sites for analytic treatment.
exclusions = (
    ("PRTA", "CYS",   6),
    ("PRTA", "CYS", 127),
    ("PRTA", "CYS",  30),
    ("PRTA", "CYS", 115),
    ("PRTA", "CYS",  64),
    ("PRTA", "CYS",  80),
    ("PRTA", "CYS",  76),
    ("PRTA", "CYS",  94),
    ("PRTA", "ARG",   0), )
electrostaticModel.Initialize (excludeResidues=exclusions)
electrostaticModel.Summary ()
electrostaticModel.SummarySites ()
electrostaticModel.WriteJobFiles ()
electrostaticModel.CalculateElectrostaticEnergies ()


sites = (
    ("PRTA", "GLU" , 35),
    ("PRTA", "ASP" , 52), )

mcModelGMCT    = MCModelGMCT    (pathGMCT="/home/mikolaj/local/bin/")
mcModelDefault = MCModelDefault ()

for mcModel, folded, direc, message, sedFile, substateFile in (
    (None           , True  , "curves_analytic"          , "analytically"             , "prob_ph7_analytic.sed"          , "substate_ph7_analytic.tex"         ),
    (mcModelGMCT    , True  , "curves_gmct"              , "using GMCT"               , "prob_ph7_gmct.sed"              , "substate_ph7_gmct.tex"             ),
    (mcModelDefault , True  , "curves_custom"            , "using custom MC sampling" , "prob_ph7_custom.sed"            , "substate_ph7_custom.tex"           ),
        ):
    electrostaticModel.DefineMCModel (mcModel)

    logFile.Text ("\n***Calculating titration curves %s***\n" % message)
    curves = TitrationCurves (electrostaticModel, curveSampling=.5)
    curves.CalculateCurves ()
    curves.WriteCurves (directory=direc)

    logFile.Text ("\n***Calculating protonation states at pH=7 %s***\n" % message)
    electrostaticModel.CalculateProbabilities (pH=7.)
    electrostaticModel.SummaryProbabilities ()
    electrostaticModel.SedScript_FromProbabilities (filename=sedFile, overwrite=True)

    logFile.Text ("\n***Calculating substate energies at pH=7 %s***\n" % message)
    substate = MEADSubstate (electrostaticModel, sites)
    substate.CalculateSubstateEnergies ()
    substate.Summary ()
    substate.Summary_ToLatex (filename=substateFile, includeSegment=True)


logFile.Text ("\n***Calculating energies of the first 10 state vectors***\n")
table = logFile.GetTable (columns=[6, 16])
table.Start ()
table.Heading ("State")
table.Heading ("Gmicro")

vector = StateVector (electrostaticModel)
vector.Reset ()
for i in range (10):
    Gmicro = electrostaticModel.CalculateMicrostateEnergy (vector, pH=7.)
    vector.Increment ()
    table.Entry ("%d" % (i + 1))
    table.Entry ("%f" % Gmicro)
table.Stop ()


logFile.Footer ()
#    (None           , False , "curves_analytic_unfolded" , "analytically (unfolded)"  , "prob_ph7_analytic_unfolded.sed" , "substate_ph7_analytic_unfolded.tex"),
