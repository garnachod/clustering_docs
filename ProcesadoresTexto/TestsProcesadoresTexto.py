# -*- coding: utf-8 -*-
#import os
#import sys
#lib_path = os.path.abspath('../')
#sys.path.append(lib_path)
from DBbridge.ConsultasCassandra import ConsultasCassandra
from GenerateVectorsFromTweets import GenerateVectorsFromTweets
import time


if __name__ == '__main__':
	consultas = ConsultasCassandra()

	tweets = consultas.getTweetsUsuarioCassandra_statusAndLang(11688082)
	generator = GenerateVectorsFromTweets()
	time_ini = time.time()
	print generator.getVector_topics(tweets, 'ar')
	print "Tiempo carga y generacion: " + str(time.time() - time_ini)

	time_ini = time.time()
	print generator.getVector_topics(tweets, 'ar')
	print "Tiempo generacion: " + str(time.time() - time_ini)