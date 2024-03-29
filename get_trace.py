import os
import sys
sys.path.append(os.path.dirname(sys.path[0]))

import json
# from ethereumetl.json_rpc_requests import generate_trace_transaction_json_rpc
# from ethereumetl.utils import rpc_response_to_result
from rpc import BatchHTTPProvider


def is_retriable_error(error_code):
    if error_code is None:
        return False
    if not isinstance(error_code, int):
        return False
    # https://www.jsonrpc.org/specification#error_object
    if error_code == -32603 or (-32000 >= error_code >= -32099):
        return True
    return False


def generate_json_rpc(method, params, request_id=1):
    return {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': request_id,
    }


def generate_trace_transaction_json_rpc(tx_hashes: list[str]):
    """Get op code from tx hashes, by calling 'debug_traceTransaction'.
    Currently, Chainnodes.org's free tier offer support for this function"""
    for idx, tx_hash in enumerate(tx_hashes):
        yield generate_json_rpc(
            method='debug_traceTransaction',
            params=[
                tx_hash,
                # {'tracer': 'prestateTracer'}
            ],
            request_id=idx
        )


def get_vm_traces(tx_hashes: list[str]) -> dict[str, str]:
    provider_url = 'https://mainnet.chainnodes.org/YOUR-API-KEY'

    _batch_provider = BatchHTTPProvider(provider_url)
    trace_tx_rpc = list(generate_trace_transaction_json_rpc(tx_hashes))

    responses = _batch_provider.make_batch_request(json.dumps(trace_tx_rpc))

    opcodes_dict: dict = dict()
    try:
        for response_item in responses:
            result = response_item.get('result', None)  # there might be errors, need retrying

            op_code = result['structLogs']
            opcodes_dict[tx_hashes[response_item['id']]] = op_code

    except Exception as ex:
        raise ex

    return opcodes_dict


def main():
    transaction_hashes = ['0x903479395df67ad9fdb8a1b0e71d0d0232c5eb7733f86fe395e2a8ed1761d4fc',
                          '0xdde9161e0eda14a987b8579ee204d72c8c51c858ed90cbc2b411acc1a420c2d5']
    op_codes = get_vm_traces(tx_hashes=transaction_hashes)
    print(op_codes)


if __name__ == '__main__':
    main()
