This script is used for editing URL maps in a more robust fashion than that allowed with 'GCloud compute url-maps edit'. It is most useful for appending path rules to an existing path matcher, which is something the GCloud tool does not currently support.
# Usage
```
usage: urlmap-editor.py [-h] --pathmatcher PATHMATCHER [PATHMATCHER ...]
                        --pathrules PATHRULES [PATHRULES ...] --hostrule
                        HOSTRULE [HOSTRULE ...] --file FILE

optional arguments:
  -h, --help            show this help message and exit
  --pathmatcher PATHMATCHER [PATHMATCHER ...]
                        path matcher parameters (name/defaultService)
  --pathrules PATHRULES [PATHRULES ...]
                        path rule parameters (path/service)
  --hostrule HOSTRULE [HOSTRULE ...]
                        host rule parameters (hosts/pathMatcher)
  --file FILE           The filename of the URL map to use

An URL map editor for manipulating host rules and path matchers. All denoted
parameters i.e., hostrule parameters take key=value pairs. All supplementary
parameters denoted as valid for various options i.e., defaultService for
--pathmatcher, are required.
````
## Notes and examples
The syntax defined above very much resembles the keys as defined in the exported copy of a URL map i.e., defaultService. As an example, the below would add a defaultService rule to a path matcher called foomatcher, associated to the host 'example.com' which points to a backend bucket called foo-bucket:
```
$ ./urlmap-editor.py --hostrule hosts=example.com pathMatcher=foomatcher --pathmatcher name=foomatcher defaultService=https://www.googleapis.com/compute/v1/projects/$project/global/backendBuckets/foobucket --file foomap.yaml
```
Another example, this time we add a path rule pointing to a backend bucket called bar-bucket:
```
$ ./urlmap-editor.py --hostrule hosts=example.com --pathmatcher name=foomatcher --pathmatcher name=foomatcher defaultService=https://www.googleapis.com/compute/v1/$project/global/backendBuckets/foo-bucket --pathrules path=/bar/* service=https://www.googleapis.com/compute/v1/projects/$project/global/backendBuckets/bar-bucket --file=foomap.yaml
```
And later on, you can append another path rule to a backend bucket called 'baz-bucket' and retain the same path matcher:
```
$ ./urlmap-editor.py --hostrule hosts=example.com --pathmatcher name=foomatcher --pathmatcher name=foomatcher defaultService=https://www.googleapis.com/compute/v1/$project/global/backendBuckets/foo-bucket --pathrules path=/baz/* service=https://www.googleapis.com/compute/v1/projects/$project/global/backendBuckets/baz-bucket --file=foomap.yaml
```
Make sure to substitute '$project' with your actual GCP project ID.