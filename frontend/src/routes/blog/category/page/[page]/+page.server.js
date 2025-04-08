import { redirect } from '@sveltejs/kit';
import { postsPerPage } from '$lib/blog/config'
import fetchPosts from '$lib/blog/assets/js/fetchPosts'

export const load = async ({ fetch, params }) => {
  const page = parseInt(params.page) || 1

  // Keeps from duplicationg the blog index route as page 1
  if (page <= 1) {
    redirect(301, '/blog');
  }
  
  let offset = (page * postsPerPage) - postsPerPage

  const totalPostsRes = await fetch('/blogapi/posts/count')
  const total = await totalPostsRes.json()
  const { posts } = await fetchPosts({ offset, page })

  return {
    posts,
    page,
    totalPosts: total 
  }
}
