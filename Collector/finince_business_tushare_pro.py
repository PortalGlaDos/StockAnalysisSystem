import pandas as pd
import tushare as ts
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
except Exception as e:
    sys.path.append(root_path)

    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

FIELDS = {
    'Finance.MainBusinessComposition': {
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'finance_business_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

def __fetch_business_data(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        since_limit = years_ago_of(until, 5)
        since = max([since, since_limit])

        # Because of the implementation of this interface, we only fetch the annual report
        since_year = since.year
        until_year = until.year

        result = None
        pro = ts.pro_api(config.TS_TOKEN)

        clock = Clock()
        for year in range(since_year, until_year):
            ts_date = '%02d1231' % year
            sub_result = pro.fina_mainbz(ts_code=ts_code, start_date=ts_date, end_date=ts_date)
            result = pd.concat([result, sub_result])
        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

        result.fillna(0.0)
        del result['ts_code']

        result = pd.DataFrame({'business': result.groupby('end_date').apply(
            lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        result['ts_code'] = ts_code

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.fillna('')
        result['period'] = pd.to_datetime(result['end_date'])
        result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_business_data(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

