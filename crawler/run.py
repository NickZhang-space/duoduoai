"""
爬虫入口脚本
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='拼多多爬虫')
    parser.add_argument('--task', choices=['trends', 'competitors'], required=True, help='任务类型')
    args = parser.parse_args()
    
    if args.task == 'trends':
        print('启动类目趋势爬虫...')
        from .pdd_search import crawl_category_trends
        crawl_category_trends()
    elif args.task == 'competitors':
        print('启动竞品监控爬虫...')
        from .pdd_product import crawl_competitors
        crawl_competitors()

if __name__ == '__main__':
    main()
