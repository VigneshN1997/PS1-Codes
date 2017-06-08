from django.shortcuts import render
from django.http import HttpResponseRedirect
from elasticsearch import Elasticsearch		
import re

from .forms import SearchForm

es = Elasticsearch(['http://elsearch:changeit@localhost:9200'])


def get_search(request):
	#if the search button is pressed, it is a POST request
	if request.method == 'POST':
		form = SearchForm(request.POST)
		if form.is_valid():
			#retrieving the query text in search box
			query = form.cleaned_data['query']
			print(query)
			select = request.POST['select']
			if(select=="all"):
				select = ""

			suggestion = {
				"entity-suggest": {
					"text": query,
					"term": {
						"analyzer": "standard",
						"field":"name"
					},
					"term": {
						"analyzer": "standard",
						"field": "altnames"
					},
					"term": {
						"analyzer": "standard",
						"field": "content"
					},
					"term": {
						"analyzer": "standard",
						"field": "tags"
					}
				}
			}
			res = es.suggest(body=suggestion, index='nroer_pro')
			print(res)
			if(len(res['entity-suggest'][0]['options'])>0):
				query = (res['entity-suggest'][0]['options'][0])['text']
			res = es.search(index="nroer_pro",doc_type=select, body={"query": {
																			"multi_match": {
																				"query" : query,
																				"type": "best_fields",
																				#"fuzziness": "AUTO",
																				"fields": ["name^2", "altnames", "content", "tags"],
																				"minimum_should_match": "30%"
																				}
																			},
																	"rescore": {
																		"window_size": 50,
																		"query": {
																			"rescore_query": {
																				"bool": {
																					"should": [
																						{"match_phrase": {"name": { "query": query, "slop":50}}},
																						{"match_phrase": {"altnames": { "query": query, "slop": 50}}},
																						{"match_phrase": {"content": { "query": query, "slop": 50}}}
																					]
																				}
																			}
																		}
																	}
																})
			hits = "No of docs found: %d" % res['hits']['total']
			res_list = ['Showing results for %s :' % query, hits]
			#med_list is the list which will be passed to the html file.
			med_list = []
			for doc in res['hits']['hits']:
				#if(doc['_source']['if_file'] in doc['_source'].keys()):
					# if(doc['_source']['if_file']['original']['relurl'] is not None):
					# 	med_list.append()					
				if('if_file' in doc['_source'].keys()):
					s = doc['_source']['name']
					if '.' in s:
						l = s.index('.')
					else:
						l = len(s)
					med_list.append([doc['_id'],s[0:l],doc['_source']['if_file']['original']['relurl'],doc['_score']])	#printing only the id for the time being along with the node name
				else:
					med_list.append([doc['_id'],doc['_source']['name'],None,doc['_score']])

			return render(request, 'esearch/basic.html', {'header':res_list, 'content': med_list})
	#if the search page is loaded for the first time
	else:
		form = SearchForm()

	return render(request, 'esearch/sform.html', {'form':form})
