# -*- coding: utf-8 -*-
import json
import scrapy
from scrapy import Request
from xpc.items import XpcItem, CommentItem, ComposerItem,CopyrightItem

comment_api = "http://www.xinpianchang.com/article/filmplay/ts-getCommentApi/id-%s/page-1"
vip_map = {
    'yellow-v': 1,
    'blue-v': 2,
}
def ci(s):
    if isinstance(s, int):
        return s
    return int(s.replace(',', '')) if s else 0

class DiscoverySpider(scrapy.Spider):
    name = 'discovery'
    root_url = 'http://www.xinpianchang.com'
    allowed_domains = ['www.xinpianchang.com']
    # start_urls = ['http://www.xinpianchang.com/channel/index/id-0/sort-like']
    start_urls = ['http://www.xinpianchang.com/channel/index/id-0/sort-like/type-0?from=articleListPage']


    def parse(self, response):
        post_url = "http://www.xinpianchang.com/a%s?from=ArticleList"
        post_list = response.xpath('//ul[@class="video-list"]/li')
        for post in post_list:
            post_id = post.xpath('./@data-articleid').extract_first()
            thumbnail = post.xpath('./a/img/@_src').get()
            request = Request(post_url % post_id,callback=self.parse_post)
            request.meta['pid'] = post_id   # 使用此方法携带pid一起发送请求
            request.meta['thumbnail'] = thumbnail
            yield request

        # 作品最新页面的下一页
        next_page = response.xpath('//div[@class="page"]/a[last()]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_post(self, response):

        post = XpcItem()
        post['pid'] = response.meta['pid']
        post['thumbnail'] = response.meta['thumbnail']
        post['title'] = response.xpath('//div[@class="title-wrap"]/h3/text()').get()
        post['preview'] = response.xpath('//div[@class="filmplay"]//img/@src').get()
        post['video'] = response.xpath('//video[@id="xpc_video"]/@src').get()
        post['video_format'] = ''
        post['category'] = response.xpath('//span[@class="cate v-center"]/text()').get()
        post['created_at'] = response.xpath('//span[contains(@class,"update-time")]/i/text()').get()
        post['play_counts'] = response.xpath('//i[contains(@class,"play-counts")]/@data-curplaycounts').get()
        post['like_counts'] = ci(response.xpath('//span[contains(@class,"like-counts")]/@data-counts').get())
        post['description'] = response.xpath('//p[contains(@class,"desc")]/text()').get()
        yield post

        creator_list = response.xpath('//div[contains(@class,"filmplay-creator")]/ul[@class="creator-list"]/li')

        for creator in creator_list:
            user_page = creator.xpath('./a/@href').get()
            user_id = creator.xpath('./a/@data-userid').get()
            request = Request('%s%s' % (self.root_url, user_page), callback=self.parse_composer)
            request.meta['cid'] = user_id
            yield request
            cr = CopyrightItem()
            cr['pid'] = response.meta['pid']
            cr['cid'] = user_id
            cr['pcid'] = '%s_%s' % (cr['pid'], cr['cid'])
            cr['roles'] = creator.xpath('.//span[contains(@class, "roles")]/text()').get()
            yield cr
        request = Request(comment_api % post['pid'],callback=self.parse_comment)
        request.meta['pid']=post['pid']
        # request.meta['cur_page'] = 1
        yield request

    def parse_comment(self, response):
        if response.text:
            pid = response.meta['pid']
            result = json.loads(response.text)
            next_page = result['data']['next_page_url']
            if next_page:
                request = Request(next_page,callback=self.parse_comment)
                request.meta['pid'] = pid
                yield request

            comments = result['data']['list']
            for c in comments:
                comment = CommentItem()
                comment['commentid'] = c['commentid']
                comment['pid'] = pid
                comment['cid'] = c['userInfo']['userid']
                comment['uname'] = c['userInfo']['username']
                comment['avatar'] = c['userInfo']['face']
                comment['created_at'] =ci(c['addtime_int'])
                comment['content'] = c['content']
                comment['like_counts'] = ci(c['count_approve'])
                if c['reply']:
                    comment['reply'] = c['reply']['commentid'] or 0
                yield comment

                request = Request('%s/u%s'%(self.root_url, comment['cid']),callback=self.parse_composer)
                request.meta['cid'] = comment['cid']
                yield request

            # total_pages = response.xpath('/li[last()]/@data-totalpages').get()
            # cur_page = response.meta['cur_page']
            # pid = response.meta['pid']
            # if total_pages and total_pages.isdigit():
            #     total_pages = int(total_pages)
            #
            #     if total_pages>cur_page:
            #         request = Request(comment_api % (response.meta['pid'],cur_page+1),callback=self.parse_comment)
            #         request.meta['pid'] = response.meta['pid']
            #         request.meta['cur_page'] = cur_page+1
            #         yield request
            # comments = response.xpath('//li')
            # for comment in comments:
            #     c =  CommentItem()
            #     user_page = '%s%s' % (self.root_url, comment.xpath('./a[1]/@href').get())
            #     userid = comment.xpath('//span[@class="head-wrap"]/@data-userid').get()
            #     request = Request(user_page,callback=self.parse_composer)
            #     request.meta['cid'] = userid
            #     yield request
            #     c['cid'] = userid
            #     c['pid'] = pid
            #     c['created_at'] = comment.xpath('.//span[contains(@class,"send-time")]/text()').get()
            #     c['content'] = comment.xpath('.//div[contains(@class,"comment-con")]/text()').get()
            #     c['like_counts'] = comment.xpath('.//i[@class="counts"]/text()').get()
            #     yield c

    def parse_composer(self,response):
        composer = ComposerItem()
        composer['cid'] = response.meta['cid']
        composer['banner'] = response.xpath('//div[@class="banner-wrap"]/@style').get()
        if composer['banner']:
            # 提取样式中的图片链接
            composer['banner'] = composer['banner'][21:-1]
        elem = response.xpath('//span[@class="avator-wrap-s"]')
        composer['avatar'] = elem.xpath('./img/@src').get()
        auth_style = elem.xpath('./span/@class').get()
        if auth_style:
            composer['verified'] =vip_map.get(auth_style.split(' ')[-1], 0)
        composer['name'] = response.xpath('//p[contains(@class,"creator-name")]/text()').get()
        composer['intro'] = response.xpath('//p[contains(@class,"creator-desc")]/text()').get()
        composer['like_counts'] = ci(response.xpath('//span[contains(@class,"like-counts")]/text()').get())
        composer['fans_counts'] = ci(response.xpath('//span[contains(@class,"fans-counts")]/text()').get())
        composer['follow_counts'] = ci(response.xpath('//span[@class="follow-wrap"]/span[last()]/text()').get())
        yield composer