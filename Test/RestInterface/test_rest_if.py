import traceback
import datetime

from StockAnalysisSystem.interface.interface_rest import RestInterface


class TestWrapper:
    LINE_LENGTH = 100

    def __init__(self, name: str):
        self.__test_name = name
        self.__test_start = datetime.datetime.now()

    def __enter__(self):
        self.print_in_splitter_mid('-', self.__test_name)
        self.__test_start = datetime.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_str = 'Time spending: %s ms' % ((datetime.datetime.now() - self.__test_start).total_seconds() * 1000)
        self.print_in_splitter_mid(' ', time_str)
        print('')

    @staticmethod
    def print_in_splitter_mid(splitter:str, text: str):
        prefix = splitter * ((TestWrapper.LINE_LENGTH - 2 - len(text)) // 2)
        surfix = splitter * (TestWrapper.LINE_LENGTH - 2 - len(prefix) - len(text))
        print('%s %s %s' % (prefix, text, surfix))


def main():
    caller = RestInterface()
    caller.if_init(api_uri='http://127.0.0.1:80/api', token='xxxxxx')

    with TestWrapper('sas_query'):
        df = caller.sas_query('Market.SecuritiesInfo', '000001.SZSE')
        print(df)

    with TestWrapper('sas_query'):
        df = caller.sas_query('Finance.IncomeStatement', '000001.SZSE', ('2000-01-01', '2020-12-31'), readable=True)
        print(df)

    with TestWrapper('sas_get_all_uri'):
        uris = caller.sas_get_all_uri()
        print(uris)

    with TestWrapper('sas_get_data_range'):
        _range = caller.sas_get_data_range('Finance.IncomeStatement', '000001.SZSE')
        print(_range)

    with TestWrapper('update_range'):
        update_range = caller.sas_calc_update_range('Finance.IncomeStatement', '000001.SZSE')
        print(update_range)

    with TestWrapper('sas_get_data_agent_probs'):
        agents = caller.sas_get_data_agent_probs()
        print(agents)

    with TestWrapper('sas_get_data_agent_update_list'):
        update_list = caller.sas_get_data_agent_update_list('Finance.IncomeStatement')
        print(update_list)

    with TestWrapper('sas_get_local_data_range_from_update_table'):
        data_range = caller.sas_get_local_data_range_from_update_table(['Finance', 'IncomeStatement', '000001.SZSE'])
        print(data_range)

    with TestWrapper('sas_get_last_update_time_from_update_table'):
        last_update = caller.sas_get_last_update_time_from_update_table(['Finance', 'IncomeStatement', '000001.SZSE'])
        print(last_update)

    with TestWrapper('sas_get_analyzer_probs'):
        analyzer_probs = caller.sas_get_analyzer_probs()
        print(analyzer_probs)

    with TestWrapper('sas_get_stock_info_list'):
        stock_info_list = caller.sas_get_stock_info_list()
        print(stock_info_list)

    with TestWrapper('sas_get_stock_identities'):
        stock_identities = caller.sas_get_stock_identities()
        print(stock_identities)

    with TestWrapper('sas_guess_stock_identities'):
        stock_identities = caller.sas_guess_stock_identities('000001')
        print(stock_identities)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass

