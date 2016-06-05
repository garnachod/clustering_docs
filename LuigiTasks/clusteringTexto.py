from Config.Conf import Conf
from entrenamientoTexto import TrainDoc2Vec
from random import randint, random
from extraccion import LimpiadorFromCrawler
from ProcesadoresTexto.Doc2Vec import Doc2Vec, LabeledLineSentence
import luigi
import numpy as np
import json
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage


class ClusteringDoc2Vec(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.clusteringTexto ClusteringDoc2Vec --carpeta PATH
	"""
	"""
		Random hierarchical clustering Programed
	"""
	carpeta = luigi.Parameter()

	def requires(self):
		return TrainDoc2Vec(self.carpeta)

	def output(self):
		return luigi.LocalTarget('%s/clustering/file.txt'%self.carpeta)

	def clustersDistance(self, cluster1, cluster2, dicDocs):
		maxDistance = 2000.0
		for elem1 in cluster1:
			vecElem1 = dicDocs[elem1]
			for elem2 in cluster2:
				#print vecElem1
				#print dicDocs[elem2]
				dist = self.disFun(vecElem1, dicDocs[elem2])
				#print dist
				if dist < maxDistance:
					maxDistance = dist

		return maxDistance

	def setDistanceFun(self):
		self.disFun = lambda x, y: (np.dot(x, np.array([y]).T))[0]

	def clusteringRun(self, dicDocs):
		self.setDistanceFun()
		#initialization
		#generate 1 cluster per file
		clustersEpoch = []
		for tag in dicDocs:
			clustersEpoch.append([tag])

		clustersEpochs = []
		distancesEpochs = []
		clustersEpochs.append(clustersEpoch)
		#get the number of cluster of the last epoch
		nClusters = len(clustersEpochs[len(clustersEpochs) - 1])
		while nClusters > 1:
			betterDist = 0.0
			betterClusterIndex = -1
			clusterToJoinIndex = randint(0, nClusters-1)
			clustersEpoch = []
			for i, clusterToCompare in enumerate(clustersEpochs[len(clustersEpochs) - 1]):
				if i != clusterToJoinIndex:
					distance = self.clustersDistance(clustersEpochs[len(clustersEpochs) - 1][clusterToJoinIndex], clusterToCompare, dicDocs)
					clustersEpoch.append(clusterToCompare)
					if distance > betterDist:
						betterDist = distance
						betterClusterIndex = len(clustersEpoch) - 1

			for elem in clustersEpochs[len(clustersEpochs) - 1][clusterToJoinIndex]:
				clustersEpoch[betterClusterIndex].append(elem)
			
			distancesEpochs.append(betterDist)
			clustersEpochs.append(clustersEpoch)
			nClusters -= 1

		return clustersEpochs, distancesEpochs


	def run(self):
		d2v = Doc2Vec()
		input_path = self.input().path.replace("txt", "d2v")
		d2v.loadModel(input_path)
		dicDocs = d2v.getNormalizedTagsVectors()
		clustersEpochs, distancesEpochs = self.clusteringRun(dicDocs)
		#print distancesEpochs
		#print clustersEpochs[len(clustersEpochs) - 3]
		with self.output().open("w") as fout:
			fout.write(json.dumps(clustersEpochs))

		with open(self.output().path.replace("txt", "vecs"), "w") as fout:
			for tag in dicDocs:
				fout.write(str(dicDocs[tag]).replace("\n", "  ").replace("[", "").replace("]", "") )
				fout.write("\n")


class ClusteringDoc2VecScipy(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.clusteringTexto ClusteringDoc2VecScipy --carpeta PATH
	"""
	"""
		https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/
	"""
	carpeta = luigi.Parameter()

	def requires(self):
		return TrainDoc2Vec(self.carpeta)

	def output(self):
		return luigi.LocalTarget('%s/clustering/file.txt'%self.carpeta)

	def run(self):
		d2v = Doc2Vec()
		input_path = self.input().path.replace("txt", "d2v")
		d2v.loadModel(input_path)
		dicDocs = d2v.getNormalizedTagsVectors()
		y = []
		indexToClus = []
		labels=[]
		for dicDoc in dicDocs:
			y.append(dicDocs[dicDoc])
			indexToClus.append([dicDoc])

			if random() > 0.95:
				labels.append(dicDoc[:10])
			else:
				labels.append("")

		y = np.array(y)

		Z = linkage(y, method='complete', metric='cosine')

		plt.figure(figsize=(25, 10))
		plt.title('Hierarchical Clustering Dendrogram')
		plt.xlabel('sample index')
		plt.ylabel('distance')
		dendrogram(
		    Z,
		    leaf_rotation=90.,  # rotates the x axis labels
		    leaf_font_size=8.,  # font size for the x axis labels
		    labels = labels
		)



		#print Z
		#with self.output().open("w") as fout:
		#	fout.write(json.dumps(clustersEpochs))
		"""
		linkage matrix:
			primera fila id cluster
			segunda fila id cluster
			distancia
			nO de nodos en el cluster

			los nuevos clusters van creciendo en ID desde los creados inicialmente.
		"""
		countClusters = 0
		clustersEpochs = [{} for _ in range(len(Z) + 1)]
		for i, dicDoc in enumerate(dicDocs):
			clustersEpochs[0][str(i)] = [dicDoc]
			countClusters += 1

		sort = [ (i, dicDoc) for i, dicDoc in enumerate(dicDocs)]
		sort = sorted(sort, key= lambda x:x[1])
		for i, dicDoc in sort:
			print str(i) + "->" + dicDoc

		for i, line in enumerate(Z):
			idC1 = line[0] #primera fila id cluster
			idC2 = line[1] #segunda fila id cluster
			for clusterid in clustersEpochs[i]:
				if clusterid != str(int(idC1)) and clusterid != str(int(idC2)):
					clustersEpochs[i + 1][clusterid] = clustersEpochs[i][clusterid]

			clustersEpochs[i + 1][str(countClusters)] = clustersEpochs[i][str(int(idC1))] + clustersEpochs[i][str(int(idC2))]
			countClusters += 1

		finalClustersEpochs = []
		for clustersEpoch in clustersEpochs:
			temp = []
			for elem in clustersEpoch:
				temp.append(clustersEpoch[elem])
			finalClustersEpochs.append(temp)

		with self.output().open("w") as fout:
			fout.write(json.dumps(finalClustersEpochs))

		plt.savefig(self.output().path.replace("txt", "eps"), format='eps', dpi=300)
		



"""
class ViewClusters(luigi.Task):
	

	def run(self):
		# calculate full dendrogram
		

"""
class ShowInfoClusters(luigi.Task):
	"""
		command line usage:
			luigi --module LuigiTasks.clusteringTexto ShowInfoClusters --carpeta PATH --nclust 2

		computa las palabras mas frecuentes dentro del cluster
	"""
	carpeta = luigi.Parameter()
	nclust = luigi.Parameter()

	def requires(self):
		return [ClusteringDoc2VecScipy(self.carpeta), LimpiadorFromCrawler(self.carpeta)]

	def output(self):
		return luigi.LocalTarget('%s/clustering/interpretacion_%s.txt'%(self.carpeta, self.nclust))

	def getClusterOfFile(self, clusters, nameFile):
		for i, cluster in enumerate(clusters):
			for file in cluster:
				if nameFile in file:
					return i

		return "ERROR"

	def dictionaryToTupleArray(self, dictionary):
		array = []
		for elem in dictionary:
			array.append((elem, dictionary[elem]))

		return array

	def run(self):
		clustersEpochs = None
		stringsPath = None
		for _input in self.input():
			if "clustering/file.txt" in _input.path:
				with _input.open("r") as fin:
					clustersEpochs = json.loads(fin.read())
			else:
				stringsPath = _input.path

		clusters = clustersEpochs[len(clustersEpochs) - (int(self.nclust) + 1)]
		#print clusters
		lab = LabeledLineSentence(stringsPath, ides="String")
		clusters_info = [{} for i in range(int(self.nclust) + 1)]

		for text, labels in lab:
			label = labels[0]
			cluster_id = self.getClusterOfFile(clusters, label)
			#print cluster_id
			for palabra in text:
				if len(palabra) > 1:
					if palabra not in clusters_info[cluster_id]:
						clusters_info[cluster_id][palabra] = 0

					clusters_info[cluster_id][palabra] += 1



		for i, cluster in enumerate(clusters_info):
			print "\nCluster " + str(i)
			tuples = self.dictionaryToTupleArray(cluster)
			sorted_tuples = sorted(tuples, key=lambda x: x[1], reverse=True)[:100]
			for tupl in sorted_tuples:
				print tupl[0] + "\t" + str(tupl[1])



		