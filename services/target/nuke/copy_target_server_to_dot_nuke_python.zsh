#!/bin/zsh -fx

SAFETY=
# SAFETY=echo

SERVER_ROOT=${HOME}/.nuke/python
GRPC_SUBDIR=services/target/nuke

${SAFETY} cp -p ${GRPC_SUBDIR}/server.py ${SERVER_ROOT}
${SAFETY} mkdir -p ${SERVER_ROOT}/${GRPC_SUBDIR}
${SAFETY} cp -p ${GRPC_SUBDIR}/target_pb2.py ${SERVER_ROOT}/${GRPC_SUBDIR}
${SAFETY} cp -p ${GRPC_SUBDIR}/target_pb2_grpc.py ${SERVER_ROOT}/${GRPC_SUBDIR}
${SAFETY} cp -p services/ports.py ${SERVER_ROOT}/services
