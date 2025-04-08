import { postsPerPage } from '$lib/blog/config'
import fetchPosts from '$lib/blog/assets/js/fetchPosts'
import { json } from '@sveltejs/kit'

export const prerender = true

export const GET = async () => {
  const options = {
    limit: postsPerPage
  }

  const { posts } = await fetchPosts(options)
  return json(posts)
}