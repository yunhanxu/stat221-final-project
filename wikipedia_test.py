from lda import LDA, convert_doc, remove_word
from wikirandom import get_random_wikipedia_articles

import numpy as np
import sys
from sklearn.feature_extraction.text import CountVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
#from sklearn.decomposition import LatentDirichletAllocation as LDAsklearn
#import gensim
import time

with open(sys.path[0] + '\\dict.txt', 'r') as f:
    vocab_list = [s[:-1] for s in f.readlines()]
vectorizer = CountVectorizer(vocabulary=vocab_list)

D = 3.3e6 # fix this
V = len(vectorizer.vocabulary)
n_topics = int(sys.argv[1])
batch_size = int(sys.argv[2])
n_iter = int(sys.argv[3])
lda = LDA(n_topics, D, V, 1./n_topics, 1./n_topics, 1, 0.51)

elbo_lst = []
scrape_time = 0.
train_time = 0.
examples = []
log_likelihoods = []
for t in range(n_iter):
    print '====================BATCH %d====================' % t
    sys.stdout.flush()
    start_time = time.time()
    articles, articlenames = get_random_wikipedia_articles(batch_size)
    end_time = time.time()
    scrape_time += end_time - start_time
    start_time = time.time()
    mat = vectorizer.transform(articles)
    mat = mat[filter(lambda d : mat[d].sum() > 1, range(mat.shape[0]))] # check for length > 1 -- need at least 2 words, to have 1 for held-out likelihood and >=1 for training
    rows = [convert_doc(mat[d]) for d in range(mat.shape[0])]
    rows, words = zip(*([remove_word(row) for row in rows]))
    rows = list(rows)
    phi, gamma = lda.batch_update2(rows, t)
    pred_log_likelihoods = [lda.predictive_log_likelihood(gamma_row, word) for gamma_row, word in zip(gamma, words)]
    print zip([vectorizer.vocabulary[word] for word in words], pred_log_likelihoods)
    log_likelihoods.append(np.mean(pred_log_likelihoods))
    extreme_row = np.argmax((gamma.T / gamma.sum(axis=1)).max(axis=0))
    extreme_row_topic = np.argmax(gamma[extreme_row])
    examples.append((articlenames[extreme_row], extreme_row_topic, (gamma.T / gamma.sum(axis=1)).max()))
    elbo_lst.append(lda.elbo(rows, phi, gamma))
    end_time = time.time()
    train_time += end_time - start_time
mean_dist = (lda.lmbda.T / lda.lmbda.sum(axis=1)).T
mean_dist_normalized = mean_dist - mean_dist.mean(axis=0)
print
print
print
print 'Total time for scraping and processing articles: %.3f seconds' % scrape_time
print 'Total time for converting data and training model: %.3f seconds' % train_time
print
print 'Representative words for each topic:'
for topic, row in enumerate(mean_dist_normalized):
    print '%d:' % topic, [vocab_list[ind] for ind in sorted(range(len(row)), key = lambda ind : -row[ind])[0:20]]
print
print 'Most popular words for each topic:'
for topic, row in enumerate(mean_dist):
    print '%d:' % topic, [vocab_list[ind] for ind in sorted(range(len(row)), key = lambda ind : -row[ind])[0:20]]
print
print 'Examples of articles from each topic:'
for topic in set(zip(*examples)[1]):
    print '%d:' % topic, [tup[0] + ' (%.1f%%)' % (100*tup[2]) for tup in examples if tup[1]==topic]
if len(log_likelihoods) < 100:
    print
    print 'Log likelihoods:', log_likelihoods
if len(elbo_lst) < 100:
    print
    print 'ELBOs:', elbo_lst
sys.stdout.flush()
plt.plot(log_likelihoods)
plt.show()
plt.plot(elbo_lst)
plt.show()