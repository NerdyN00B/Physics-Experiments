print("Enter location of file to be cleaned:")
inputFilePath = input() #"VB8012-307155C_2019-02-12_13-23-14.csv"
print("Enter output location")
outputFilePath = input() #"CleanData.csv"

file = open(inputFilePath)
uncleanDataByLine = []
for line in file:
	uncleanDataByLine.append(line.replace(',,',''))
cleanDataByLine = uncleanDataByLine[22:]
cleanData = ""
for line in cleanDataByLine:
	cleanData += line

writeFile = open(outputFilePath, 'w')
writeFile.write(cleanData)

print("Done.")