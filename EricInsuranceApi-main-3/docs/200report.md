# Basic Coverage

## Employee Count
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Amount]>0,1,0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Amount]>0,1,0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Amount]>0,1,0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Amount]>0,1,0))

## Employee Volume
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Amount]>0,[Participant_BLife_Amount],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Amount]>0,[Participant_BLife_Amount],0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Amount]>0,[Participant_BLife_Amount],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Amount]>0,[Participant_BLife_Amount],0))

## Employee Premium
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Prem]>0,[Participant_BLife_Prem],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Prem]>0,[Participant_BLife_Prem],0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Prem]>0,[Participant_BLife_Prem],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Prem]>0,[Participant_BLife_Prem],0))

## Accidental Death && Disab
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_ADD_Prem]>0,[Participant_BLife_ADD_Prem],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_ADD_Prem]>0,[Participant_BLife_ADD_Prem],0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_ADD_Prem]>0,[Participant_BLife_ADD_Prem],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_ADD_Prem]>0,[Participant_BLife_ADD_Prem],0))

## Dependent Units
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Dep_Units]>0,[Participant_BLife_Dep_Units],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Dep_Units]>0,[Participant_BLife_Dep_Units],0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Dep_Units]>0,[Participant_BLife_Dep_Units],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Dep_Units]>0,[Participant_BLife_Dep_Units],0))

## Dependent Premium
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Dep_Prem]>0,[Participant_BLife_Dep_Prem],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Dep_Prem]>0,[Participant_BLife_Dep_Prem],0)) 
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Dep_Prem]>0,[Participant_BLife_Dep_Prem],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Dep_Prem]>0,[Participant_BLife_Dep_Prem],0))

## BASIC COVERAGE TOTALS
* SHAR: =Sum(IIf(Left([Participant_Division],4)="SHAR" And [Participant_BLife_Total]>0,[Participant_BLife_Total],0))
* SHIP: =Sum(IIf(Left([Participant_Division],4)="SHIP" And [Participant_BLife_Total]>0,[Participant_BLife_Total],0))
* SHOP: =Sum(IIf(Left([Participant_Division],4)="SHOP" And [Participant_BLife_Total]>0,[Participant_BLife_Total],0))
* TOTAL: =Sum(IIf(Left([Participant_Division],4) In ("SHAR","SHIP","SHOP") And [Participant_BLife_Total]>0,[Participant_BLife_Total],0))