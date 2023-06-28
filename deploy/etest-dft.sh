#!/usr/bin/env sh

dirScripts=`dirname "${0}"`

cd ${dirScripts}/../


export TEST_IMAGE=${TEST_IMAGE:-quay.io/st4sd/official-base/st4sd-runtime-core:platform-release-latest}
docker pull ${TEST_IMAGE}

for platform in docker docker-cpu openshift openshift-kubeflux openshift-cpu
do
  echo "### Testing ${platform}"
  docker run --rm -it -v "`pwd`:/package/" -w /tmp --entrypoint sh ${TEST_IMAGE} -c \
    "etest.py --manifest=/package/dft/manifest.yaml -l20 --platform=${platform} \
    --notestExecutables /package/dft/excitation-energy-dft-gamess-us.yaml"
done