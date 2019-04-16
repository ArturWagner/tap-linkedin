import requests
import json
import singer

LOGGER = singer.get_logger()


def get_campaigns_info(account_id, header):
    campaigns = requests.get(
        'https://api.linkedin.com/v2/adCampaignsV2?q=search&s'
        'earch.account.values[0]={account_id}'.format(account_id=account_id),
        headers=header
    )
    response = json.loads(campaigns.content)
    campaigns_info = []
    for i in range(len(response['elements'])):
        campaign_info = {
            'campaign_name': response['elements'][i]['name'],
            'status': response['elements'][i]['status'],
            'id': response['elements'][i]['id'],
            'campaign_type': response['elements'][i]['type'],
            "cost_type": response['elements'][i]['costType']
        }
        campaigns_info.append(campaign_info)

    return campaigns_info


def get_campaign_metrics(params, header):
    insights = requests.get(
        'https://api.linkedin.com/v2/adAnalyticsV2?q=analytics',
        params=params,
        headers=header
        )

    return json.loads(insights.content)


def get_campaigns(config):
    account_id = 'urn:li:sponsoredAccount:' + config['account_id']
    start_date = config['start_date'].split('-')
    end_date = config['end_date'].split('-')

    header = {
        'Authorization': 'Bearer ' + config['access_token']
    }

    params = {
        'campaigns[0]': '',
        'pivot': 'CAMPAIGN',
        'dateRange.start.day': start_date[2],
        'dateRange.start.month': start_date[1],
        'dateRange.start.year': start_date[0],
        'dateRange.end.day': end_date[2],
        'dateRange.end.month': end_date[1],
        'dateRange.end.year': end_date[0],
        'timeGranularity': config['timeGranularity'],
    }

    campaigns_info = get_campaigns_info(account_id, header)
    campaigns = []
    for campaign in campaigns_info:
        try:
            campaign_id = 'urn:li:sponsoredCampaign:' + str(campaign['id'])
            params['campaigns[0]'] = campaign_id
            campaing_response = (get_campaign_metrics(params, header))
            campaing_metrics = campaing_response['elements']
            campaing_metrics[0]['campaign_name'] = campaign['campaign_name']
            campaing_metrics[0]['campaign_type'] = campaign['campaign_type']
            campaing_metrics[0]['cost_type'] = campaign['cost_type']
            campaing_metrics[0]['status'] = campaign['status']
            campaing_metrics[0]['day'] = config['start_date']
            campaigns.append(campaing_metrics[0])

        except IndexError:
            LOGGER.info('Campaing has no metrics')

    return campaigns
