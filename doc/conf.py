#
# readthedocs configuration
#

extensions = []
source_suffix = ['.rst', '.md']

master_doc = 'index'
project = u'Teachers GitLab'
copyright = '2020 - 2024'
version = 'stable'
release = 'stable'
pygments_style = 'sphinx'
htmlhelp_basename = 'teachers-gitlab'
html_theme = 'sphinx_rtd_theme'
html_sidebars = { '**': ['globaltoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html'] }
exclude_patterns = ['_build', 'venv-*', 'tests']
